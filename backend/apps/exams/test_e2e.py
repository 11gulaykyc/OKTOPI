"""İçerik → soru çözümü → kavram yanılgısı → Hata Analizi → Hata Avcısı uçtan uca akışı.

Kimlik doğrulama dahil gerçek API çağrılarıyla (force_authenticate olmadan) çalışır.
"""

from datetime import date
from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.curriculum.content_loader import get_repository

REGISTRATION = {
    "username": "deniz",
    "email": "deniz@example.com",
    "password": "GucluSifre!2026",
    "first_name": "Deniz",
    "last_name": "Kaya",
    "birth_date": date(date.today().year - 15, 1, 15).isoformat(),
    "school_type": "anadolu",
    "grade_level": 9,
}


# E-posta alan adının MX kaydı dış ağa sorulur; testte yalnızca bu DNS sorgusu taklit edilir.
@mock.patch("apps.accounts.validators._domain_accepts_mail", return_value=True)
class LearningFlowEndToEndTests(APITestCase):
    def post(self, name, data):
        return self.client.post(reverse(name), data, format="json")

    def test_full_learning_flow(self, _dns):
        repo = get_repository()

        # 1) Kayıt ve JWT ile giriş
        response = self.post("auth-register", REGISTRATION)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        response = self.post("auth-login", {"username": "deniz", "password": REGISTRATION["password"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

        # 2) Konu anlatımı etkileşimli grafikleri ve bölümleriyle gelir
        topic = self.client.get(reverse("curriculum-topic-detail", args=["top-9-tri"])).data
        viz = topic["content"]["visualizations"][0]
        self.assertEqual(viz["type"], "triangle")
        self.assertIn(viz["section_id"], [s["id"] for s in topic["content"]["sections"]])

        # 3) Soru çözümü başlar; sorular cevap anahtarı olmadan gelir
        response = self.post("exams-practice-start", {"grade": 9, "topic_id": "top-9-tri", "count": 5})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = response.data
        for q in session["questions"]:
            self.assertNotIn("step_by_step_solution", q)
            self.assertTrue(all(set(o) == {"key", "text"} for o in q["options"]))

        # 4) İlk soruya yanlış cevap: kavram yanılgısı ve önerilen bölüm döner
        target = repo.questions[session["questions"][0]["id"]]
        wrong = next(o for o in target.options if not o.is_correct)
        answer = {"session_type": "practice", "session_id": session["id"], "question_id": target.id}
        result = self.post("exams-submit-answer", {**answer, "selected_option": wrong.key}).data
        self.assertFalse(result["is_correct"])
        self.assertEqual(result["misconception"]["tag"], wrong.misconception_tag)
        recommended = result["misconception"]["recommended"]
        self.assertEqual(recommended["topic_id"], "top-9-tri")
        # Önerilen bölüm konu anlatımında gerçekten var: "Konu özetine git" bağlantısı boşa düşmez
        self.assertIn(recommended["section_id"], [s["id"] for s in topic["content"]["sections"]])

        # 5) Hata Analizi ve Gelişim Haritası bu yanlışı gösterir
        analysis = self.client.get(reverse("analytics-error-analysis")).data
        self.assertEqual(analysis["grade"], 9)
        self.assertEqual([m["question_id"] for m in analysis["mistakes"]], [target.id])
        self.assertEqual(analysis["patterns"][0]["tag"], wrong.misconception_tag)
        self.assertFalse(analysis["enough_data"])  # tek cevapla kesin tanı yok
        topic_map = next(
            t for theme in self.client.get(reverse("analytics-mastery-map")).data["themes"] for t in theme["topics"] if t["id"] == "top-9-tri"
        )
        self.assertEqual((topic_map["level"], topic_map["open_mistakes"]), ("insufficient", 1))

        # 6) Hata Avcısı oturumu yalnızca bu yanlışı içerir; doğru çözünce yanlış listeden düşer
        self.post("exams-finish", {"session_type": "practice", "session_id": session["id"]})
        hunter = self.post("exams-practice-start", {"grade": 9, "topic_id": "top-9-tri", "mistakes_only": True}).data
        self.assertEqual([q["id"] for q in hunter["questions"]], [target.id])
        retry = {"session_type": "practice", "session_id": hunter["id"], "question_id": target.id}
        self.assertTrue(self.post("exams-submit-answer", {**retry, "selected_option": target.correct_option.key}).data["is_correct"])

        analysis = self.client.get(reverse("analytics-error-analysis")).data
        self.assertEqual(analysis["mistakes"], [])
        self.assertTrue(analysis["patterns"][0]["resolved"])
        badges = self.client.get(reverse("gamification-summary")).data["badges"]
        self.assertTrue(next(b for b in badges if b["code"] == "hata-avcisi")["earned"])
