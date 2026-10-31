import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

FORBIDDEN_KEYS = ("is_correct", "misconception_tag", "misconception_detail", "recommended_subtopic_id", "step_by_step_solution")


class QuestionApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ogrenci", email="o@example.com", password="GucluSifre!2026")
        self.client.force_authenticate(self.user)

    def assert_no_answer_leak(self, response):
        raw = json.dumps(response.data, ensure_ascii=False)
        for key in FORBIDDEN_KEYS:
            self.assertNotIn(f'"{key}"', raw, f"Cevap anahtarı sızıntısı: {key}")

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(reverse("question-list")).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_hides_answer_key(self):
        response = self.client.get(reverse("question-list"), {"grade": 9})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 15)
        self.assert_no_answer_leak(response)
        self.assertEqual(set(response.data["results"][0]["options"][0]), {"key", "text"})

    def test_detail_hides_answer_key(self):
        response = self.client.get(reverse("question-detail", args=["q-9-exp-001"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["question_text"], "$-2^{-3}$ ifadesinin değeri kaçtır?")
        self.assert_no_answer_leak(response)

    def test_filter_by_topic_and_difficulty(self):
        response = self.client.get(reverse("question-list"), {"topic_id": "top-9-exp", "difficulty": "medium"})
        ids = [q["id"] for q in response.data["results"]]
        self.assertTrue(ids)
        self.assertTrue(all(q["topic_id"] == "top-9-exp" and q["difficulty"] == "medium" for q in response.data["results"]))

    def test_filter_by_subtopic(self):
        response = self.client.get(reverse("question-list"), {"subtopic_id": "top-9-tri-pyth"})
        self.assertEqual([q["id"] for q in response.data["results"]], ["q-9-tri-004"])

    def test_invalid_filters(self):
        self.assertEqual(self.client.get(reverse("question-list"), {"grade": "x"}).status_code, 400)
        self.assertEqual(self.client.get(reverse("question-list"), {"difficulty": "zor"}).status_code, 400)

    def test_unknown_question_404(self):
        self.assertEqual(self.client.get(reverse("question-detail", args=["q-9-exp-999"])).status_code, 404)
