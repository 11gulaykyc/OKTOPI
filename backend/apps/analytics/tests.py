from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.curriculum.content_loader import get_repository
from apps.gamification.models import PersonalGoal, PointLedger
from apps.gamification.services import TOPIC_COMPLETION_POINTS, level_info, total_points
from apps.study_sessions.models import DailyStudyTotal

from .models import MisconceptionLog, QuestionAttempt, TopicProgress
from .services import complete_topic, log_misconception, record_attempt

User = get_user_model()


class MisconceptionLogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.question = get_repository().questions["q-9-exp-001"]

    def option(self, key):
        return next(o for o in self.question.options if o.key == key)

    def test_wrong_option_is_logged_with_recommended_subtopic(self):
        log = log_misconception(self.user, self.question, self.option("B"))
        self.assertEqual(log.misconception_tag, "MISC_EXP_NEG_SIGN_CONFUSION")
        self.assertEqual(log.subtopic_id, "top-9-exp-sign")
        self.assertEqual(log.topic_id, "top-9-exp")
        self.assertEqual(log.selected_option, "B")

    def test_correct_option_is_not_logged(self):
        self.assertIsNone(log_misconception(self.user, self.question, self.option("C")))
        self.assertEqual(MisconceptionLog.objects.count(), 0)


class TopicProgressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_success_rate_is_none_without_data(self):
        progress = TopicProgress.objects.create(user=self.user, grade=9, topic_id="top-9-exp")
        self.assertIsNone(progress.success_rate)

    def test_success_rate(self):
        progress = TopicProgress(user=self.user, grade=9, topic_id="top-9-exp", questions_answered=4, correct_answers=3)
        self.assertEqual(progress.success_rate, 0.75)

    def test_unique_per_user_and_topic(self):
        TopicProgress.objects.create(user=self.user, grade=9, topic_id="top-9-exp")
        with self.assertRaises(IntegrityError):
            TopicProgress.objects.create(user=self.user, grade=9, topic_id="top-9-exp")

    def test_correct_cannot_exceed_answered(self):
        with self.assertRaises(IntegrityError):
            TopicProgress.objects.create(
                user=self.user, grade=9, topic_id="top-9-exp", questions_answered=1, correct_answers=2
            )


class RecordAttemptTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.question = get_repository().questions["q-9-exp-001"]

    def option(self, key):
        return next(o for o in self.question.options if o.key == key)

    def test_wrong_answer_updates_progress_and_logs_misconception(self):
        attempt, first_try = record_attempt(self.user, self.question, self.option("B"))
        self.assertTrue(first_try)
        self.assertFalse(attempt.is_correct)
        progress = TopicProgress.objects.get(user=self.user, topic_id="top-9-exp")
        self.assertEqual((progress.questions_answered, progress.correct_answers), (1, 0))
        self.assertEqual(progress.status, TopicProgress.Status.IN_PROGRESS)
        self.assertEqual(MisconceptionLog.objects.filter(user=self.user).count(), 1)

    def test_retry_does_not_inflate_success_rate(self):
        record_attempt(self.user, self.question, self.option("B"))
        _, first_try = record_attempt(self.user, self.question, self.option("C"))
        self.assertFalse(first_try)
        progress = TopicProgress.objects.get(user=self.user, topic_id="top-9-exp")
        self.assertEqual((progress.questions_answered, progress.correct_answers), (1, 0))
        self.assertEqual(QuestionAttempt.objects.filter(user=self.user).count(), 2)

    def test_blank_answer(self):
        attempt, _ = record_attempt(self.user, self.question, None)
        self.assertTrue(attempt.is_blank)
        self.assertEqual(MisconceptionLog.objects.count(), 0)


class TopicProgressApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.client.force_authenticate(self.user)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse("analytics-topic-progress", args=["top-9-exp"]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_started_by_default(self):
        response = self.client.get(reverse("analytics-topic-progress", args=["top-9-exp"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "not_started")

    def test_save_last_section(self):
        url = reverse("analytics-topic-progress", args=["top-9-exp"])
        response = self.client.patch(url, {"last_section_id": "top-9-exp-neg"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["last_section_id"], "top-9-exp-neg")
        self.assertEqual(response.data["status"], "in_progress")
        self.assertEqual(self.client.get(url).data["last_section_id"], "top-9-exp-neg")

    def test_section_must_belong_to_topic(self):
        url = reverse("analytics-topic-progress", args=["top-9-exp"])
        response = self.client.patch(url, {"last_section_id": "top-10-func-def"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_topic_404(self):
        response = self.client.get(reverse("analytics-topic-progress", args=["top-9-yok"]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_complete_awards_points_once(self):
        url = reverse("analytics-topic-complete", args=["top-9-exp"])
        first = self.client.post(url)
        second = self.client.post(url)
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["status"], "completed")
        self.assertEqual(first.data["points_awarded"], TOPIC_COMPLETION_POINTS)
        self.assertEqual(second.data["points_awarded"], 0)
        topic_entries = PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.TOPIC_COMPLETED)
        self.assertEqual(list(topic_entries.values_list("amount", flat=True)), [TOPIC_COMPLETION_POINTS])
        # Konu tamamlamak haftalık "1 konuyu tamamla" görevini de bitirir; ikinci istek hiçbir şey eklemez.
        self.assertEqual(second.data["rewards"]["points"], 0)
        self.assertEqual(first.data["rewards"]["tasks"][0]["title"], "Bu hafta 1 konuyu tamamla")

    def test_list_only_own_progress(self):
        other = User.objects.create_user(username="ayse", email="ayse@example.com", password="x")
        TopicProgress.objects.create(user=other, grade=9, topic_id="top-9-exp")
        TopicProgress.objects.create(user=self.user, grade=10, topic_id="top-10-func")
        url = reverse("analytics-topic-progress-list")
        self.assertEqual([p["topic_id"] for p in self.client.get(url).data], ["top-10-func"])
        self.assertEqual(self.client.get(url, {"grade": 9}).data, [])
        self.assertEqual(self.client.get(url, {"grade": "x"}).status_code, status.HTTP_400_BAD_REQUEST)


class DashboardSummaryApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.client.force_authenticate(self.user)
        self.url = reverse("analytics-dashboard-summary")

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_user_has_zero_stats(self):
        data = self.client.get(self.url).data
        self.assertEqual(data["study"]["total_seconds"], 0)
        self.assertEqual(data["questions"]["total"], 0)
        self.assertEqual(data["points"]["level"], 1)
        self.assertEqual(len(data["daily"]), 7)
        # Günlük ve haftalık görevler otomatik atanır; ilerleme sıfırdan başlar.
        self.assertEqual(len(data["tasks"]), 5)
        self.assertTrue(all(t["progress"] == 0 and not t["completed"] for t in data["tasks"]))

    def test_summary_reflects_real_records(self):
        repo = get_repository()
        q1, q2 = repo.questions["q-9-exp-001"], repo.questions["q-9-exp-002"]
        record_attempt(self.user, q1, next(o for o in q1.options if o.is_correct))
        record_attempt(self.user, q2, next(o for o in q2.options if not o.is_correct))
        record_attempt(self.user, q2, None)
        today = timezone.localdate()
        DailyStudyTotal.objects.create(user=self.user, date=today, active_seconds=600)
        DailyStudyTotal.objects.create(user=self.user, date=today - timedelta(days=30), active_seconds=300)
        PersonalGoal.objects.create(user=self.user, goal_type="daily_questions", target=5, valid_from=timezone.now())
        complete_topic(self.user, "top-9-exp", 9)

        data = self.client.get(self.url).data
        self.assertEqual(data["study"]["total_seconds"], 900)
        self.assertEqual(data["study"]["today_seconds"], 600)
        self.assertEqual(data["daily"][-1]["study_seconds"], 600)
        self.assertEqual(
            {k: data["questions"][k] for k in ("total", "correct", "incorrect", "blank", "today")},
            {"total": 3, "correct": 1, "incorrect": 1, "blank": 1, "today": 3},
        )
        self.assertEqual(data["daily"][-1]["questions"], 3)
        self.assertEqual(data["topics"]["completed"], 1)
        self.assertEqual(data["topics"]["success"][0]["success_rate"], 0.5)
        # Konu puanı + haftalık "1 konuyu tamamla" görevi (record_attempt tek başına puan vermez)
        complete_task = next(t for t in data["tasks"] if t["task_type"] == "complete_topic")
        self.assertTrue(complete_task["completed"])
        self.assertEqual(data["points"]["points"], TOPIC_COMPLETION_POINTS + complete_task["points_reward"])
        # Hedef ilerlemesi farklı (boş olmayan) soru sayısıdır: q1 ve q2
        self.assertEqual(data["goals"][0]["current"], 2)
        self.assertEqual(data["misconception_count"], 1)

    def test_other_users_data_is_not_included(self):
        other = User.objects.create_user(username="ayse", email="ayse@example.com", password="x")
        DailyStudyTotal.objects.create(user=other, date=timezone.localdate(), active_seconds=999)
        question = get_repository().questions["q-9-exp-001"]
        record_attempt(other, question, question.options[0])
        data = self.client.get(self.url).data
        self.assertEqual(data["study"]["total_seconds"], 0)
        self.assertEqual(data["questions"]["total"], 0)


class LevelInfoTests(TestCase):
    def test_levels(self):
        self.assertEqual(level_info(0)["level"], 1)
        self.assertEqual(level_info(99)["level"], 1)
        self.assertEqual(level_info(100)["level"], 2)
        info = level_info(200)
        self.assertEqual((info["level"], info["level_floor"], info["next_level_at"]), (2, 100, 300))
        self.assertAlmostEqual(info["progress"], 0.5)
