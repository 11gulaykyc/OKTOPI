import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import MisconceptionLog, QuestionAttempt
from apps.analytics.services import record_attempt
from apps.curriculum.content_loader import get_repository
from apps.gamification import engine
from apps.gamification.models import PointLedger, UserBadge

from .diagnostic import DIAGNOSTIC_SIZE, diagnostic_questions, level_for
from .models import StudentProfile
from .tests import make_student


def answers_for(questions, correct):
    """İlk `correct` soruyu doğru, kalanını yanlış cevaplar."""
    result = []
    for i, q in enumerate(questions):
        option = next(o for o in q.options if o.is_correct == (i < correct))
        result.append({"question_id": q.id, "selected_option": option.key})
    return result


class DiagnosticSelectionTests(APITestCase):
    def test_deterministic_and_balanced(self):
        first = [q.id for q in diagnostic_questions(9)]
        self.assertEqual(first, [q.id for q in diagnostic_questions(9)])
        self.assertEqual(len(first), DIAGNOSTIC_SIZE)
        questions = diagnostic_questions(9)
        self.assertGreaterEqual(len({q.topic_id for q in questions}), 3)
        self.assertGreaterEqual(len({q.difficulty for q in questions}), 2)

    def test_upper_grades_fall_back_to_lower_grade_questions(self):
        self.assertTrue(all(q.grade <= 11 for q in diagnostic_questions(11)))
        self.assertTrue(diagnostic_questions(11))

    def test_level_thresholds(self):
        self.assertEqual(level_for(0.2), StudentProfile.InitialLevel.BEGINNER)
        self.assertEqual(level_for(0.5), StudentProfile.InitialLevel.INTERMEDIATE)
        self.assertEqual(level_for(0.9), StudentProfile.InitialLevel.ADVANCED)


class DiagnosticApiTests(APITestCase):
    url = reverse("auth-diagnostic")

    def setUp(self):
        self.user = make_student(grade=9)
        self.client.force_authenticate(self.user)
        self.questions = diagnostic_questions(9)

    def test_get_returns_questions_without_answer_key(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["completed"])
        self.assertEqual(response.data["level"], "not_assessed")
        self.assertEqual(len(response.data["questions"]), DIAGNOSTIC_SIZE)
        body = json.dumps(response.data, default=str)
        self.assertNotIn("is_correct", body)
        self.assertNotIn("misconception", body)

    def test_submit_sets_level_and_records_attempts(self):
        response = self.client.post(self.url, {"answers": answers_for(self.questions, correct=8)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["level"], "advanced")
        self.assertEqual(response.data["user"]["profile"]["initial_level_status"], "advanced")
        self.assertIsNotNone(response.data["user"]["profile"]["initial_level_assessed_at"])
        self.assertEqual(QuestionAttempt.objects.filter(user=self.user, source="diagnostic").count(), DIAGNOSTIC_SIZE)
        # Başlangıç testi bir ölçümdür: puan, rozet ve görev ilerlemesi kazandırmaz.
        self.assertNotIn("rewards", response.data)
        self.assertFalse(PointLedger.objects.filter(user=self.user).exists())
        self.assertFalse(UserBadge.objects.filter(user=self.user).exists())
        tasks = self.client.get(reverse("gamification-tasks")).data["tasks"]
        self.assertTrue(all(t["progress"] == 0 for t in tasks))

    def test_later_practice_still_earns_first_rewards(self):
        self.client.post(self.url, {"answers": answers_for(self.questions, correct=8)}, format="json")
        question = self.questions[0]
        attempt, _ = record_attempt(self.user, question, question.correct_option)
        rewards = engine.on_answer(self.user, attempt)
        self.assertEqual([b["code"] for b in rewards.badges], ["ilk-adim"])
        self.assertTrue(PointLedger.objects.filter(user=self.user, idempotency_key=f"answer:{question.id}").exists())

    def test_wrong_answers_log_misconceptions_and_blanks_count(self):
        payload = answers_for(self.questions, correct=0)[:4]  # kalan 4 soru boş
        response = self.client.post(self.url, {"answers": payload}, format="json")
        self.assertEqual(response.data["level"], "beginner")
        self.assertEqual((response.data["correct"], response.data["total"]), (0, DIAGNOSTIC_SIZE))
        self.assertEqual(MisconceptionLog.objects.filter(user=self.user, source="diagnostic").count(), 4)
        self.assertEqual(QuestionAttempt.objects.filter(user=self.user, selected_option="").count(), 4)

    def test_can_only_be_taken_once(self):
        self.client.post(self.url, {"answers": answers_for(self.questions, correct=2)}, format="json")
        again = self.client.post(self.url, {"answers": answers_for(self.questions, correct=8)}, format="json")
        self.assertEqual(again.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(again.data["code"], "already_completed")
        self.user.profile.refresh_from_db()
        self.assertNotEqual(self.user.profile.initial_level_status, "advanced")

    def test_rejects_questions_outside_the_test(self):
        outside = next(q for q in get_repository().questions.values() if q.id not in {x.id for x in self.questions})
        response = self.client.post(self.url, {"answers": [{"question_id": outside.id, "selected_option": "A"}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(QuestionAttempt.objects.exists())

    def test_rejects_duplicate_questions(self):
        qid = self.questions[0].id
        payload = [{"question_id": qid, "selected_option": "A"}, {"question_id": qid, "selected_option": "B"}]
        response = self.client.post(self.url, {"answers": payload}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_level_cannot_be_set_via_profile_update(self):
        self.client.patch(reverse("auth-me"), {"profile": {"initial_level_status": "advanced"}}, format="json")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.initial_level_status, "not_assessed")
