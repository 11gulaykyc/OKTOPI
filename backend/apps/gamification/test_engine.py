"""Oyunlaştırma motoru: rozet kuralları, görevler, hedefler ve mükerrer ödül koruması."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import TopicProgress
from apps.analytics.services import record_attempt
from apps.curriculum.content_loader import get_repository
from apps.exams.models import TimedExamSession
from apps.study_sessions.models import DailyStudyTotal

from . import engine
from .models import Badge, DailyTask, PersonalGoal, PointLedger, UserBadge

User = get_user_model()


def answer(user, question_id, correct=True):
    question = get_repository().questions[question_id]
    option = next(o for o in question.options if o.is_correct == correct)
    attempt, _ = record_attempt(user, question, option)
    return engine.on_answer(user, attempt)


def badge_codes(user):
    return set(UserBadge.objects.filter(user=user).values_list("badge__code", flat=True))


class SeededBadgeTests(TestCase):
    def test_seven_badges_are_seeded(self):
        self.assertEqual(
            list(Badge.objects.values_list("code", flat=True)),
            ["ilk-adim", "merakli-zihin", "istikrarli-ogrenci", "hata-avcisi", "hiz-ustasi", "matematik-kasifi", "hedef-tamamlandi"],
        )


class BadgeRuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_first_step_on_first_answer_awarded_once(self):
        rewards = answer(self.user, "q-9-exp-001", correct=False)
        self.assertEqual([b["code"] for b in rewards.badges], ["ilk-adim"])
        self.assertEqual(answer(self.user, "q-9-exp-002").badges, [])
        badge_points = PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.BADGE_EARNED)
        self.assertEqual(badge_points.count(), 1)

    def test_blank_answer_is_not_first_step(self):
        question = get_repository().questions["q-9-exp-001"]
        attempt, _ = record_attempt(self.user, question, None)
        self.assertEqual(engine.on_answer(self.user, attempt).badges, [])

    def test_error_hunter_requires_previous_mistake_on_same_question(self):
        answer(self.user, "q-9-exp-002")
        self.assertNotIn("hata-avcisi", badge_codes(self.user))
        answer(self.user, "q-9-exp-001", correct=False)
        rewards = answer(self.user, "q-9-exp-001")
        self.assertIn("hata-avcisi", [b["code"] for b in rewards.badges])

    def test_explorer_needs_correct_answers_in_three_topics(self):
        answer(self.user, "q-9-exp-001")
        answer(self.user, "q-9-root-001")  # aynı konu (1.1): sayılmaz
        answer(self.user, "q-9-tri-001")
        self.assertNotIn("matematik-kasifi", badge_codes(self.user))
        # Havuzda henüz sorusu olan üçüncü bir konu yok; kuralı bir sorunun başka konuya taşınmış kopyasıyla dene.
        question = get_repository().questions["q-9-exp-002"].model_copy(update={"id": "q-9-sets-001", "topic_id": "top-9-sets"})
        attempt, _ = record_attempt(self.user, question, question.correct_option)
        engine.on_answer(self.user, attempt)
        self.assertIn("matematik-kasifi", badge_codes(self.user))

    def test_curious_mind_after_three_started_topics(self):
        # Konu anlatımı açıldı (son kalınan bölüm kaydı var) / konu tamamlandı
        TopicProgress.objects.create(user=self.user, grade=9, topic_id="top-9-exp", status="in_progress", last_section_id="top-9-exp-neg")
        TopicProgress.objects.create(user=self.user, grade=9, topic_id="top-9-root", status="completed")
        engine.on_topic_activity(self.user)
        self.assertNotIn("merakli-zihin", badge_codes(self.user))
        answer(self.user, "q-9-tri-001", correct=False)  # üçüncü konu: soru çözerek başladı
        self.assertIn("merakli-zihin", badge_codes(self.user))

    def test_diagnostic_answers_do_not_count_for_badges_or_tasks(self):
        for qid in ("q-9-exp-001", "q-9-root-001", "q-9-tri-001"):
            question = get_repository().questions[qid]
            record_attempt(self.user, question, question.correct_option, source="diagnostic")
        rewards = engine.on_topic_activity(self.user)
        self.assertEqual(rewards.badges, [])
        self.assertFalse({"merakli-zihin", "matematik-kasifi"} & badge_codes(self.user))
        tasks = {t.task_type: t for t in engine.refresh_tasks(self.user)}
        self.assertEqual(tasks["solve_questions"].progress, 0)
        self.assertEqual(tasks["correct_answers"].progress, 0)

    def test_steady_student_needs_consecutive_days(self):
        today = timezone.localdate()
        DailyStudyTotal.objects.create(user=self.user, date=today, active_seconds=600)
        DailyStudyTotal.objects.create(user=self.user, date=today - timedelta(days=2), active_seconds=600)
        engine.on_study_time(self.user)
        self.assertNotIn("istikrarli-ogrenci", badge_codes(self.user))
        DailyStudyTotal.objects.create(user=self.user, date=today - timedelta(days=1), active_seconds=100)
        engine.on_study_time(self.user)
        # 5 dakikanın altındaki gün "çalışılmış" sayılmaz.
        self.assertNotIn("istikrarli-ogrenci", badge_codes(self.user))
        DailyStudyTotal.objects.filter(user=self.user, date=today - timedelta(days=1)).update(active_seconds=400)
        engine.on_study_time(self.user)
        self.assertIn("istikrarli-ogrenci", badge_codes(self.user))

    def make_exam(self, correct=5, total=5, used_ratio=0.4, auto=False):
        start = timezone.now() - timedelta(minutes=10)
        duration = 600
        return TimedExamSession.objects.create(
            user=self.user,
            grade=9,
            question_ids=[f"q{i}" for i in range(total)],
            started_at=start,
            duration_seconds=duration,
            deadline=start + timedelta(seconds=duration),
            finished_at=start + timedelta(seconds=duration * used_ratio),
            auto_finished=auto,
            correct_count=correct,
            incorrect_count=total - correct,
        )

    def test_speed_master(self):
        too_slow = self.make_exam(used_ratio=0.6)
        too_few_correct = self.make_exam(correct=3)
        time_ran_out = self.make_exam(auto=True)
        too_short = self.make_exam(correct=4, total=4)
        for exam in (too_slow, too_few_correct, time_ran_out, too_short):
            engine.on_exam_finished(self.user, exam)
        self.assertNotIn("hiz-ustasi", badge_codes(self.user))
        engine.on_exam_finished(self.user, self.make_exam(correct=4, total=5, used_ratio=0.5))
        self.assertIn("hiz-ustasi", badge_codes(self.user))

    def test_exam_bonus_is_limited_per_day(self):
        for _ in range(engine.MAX_EXAM_BONUSES_PER_DAY + 2):
            engine.on_exam_finished(self.user, self.make_exam())
        count = PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.EXAM_COMPLETED).count()
        self.assertEqual(count, engine.MAX_EXAM_BONUSES_PER_DAY)

    def test_same_exam_finished_twice_awards_bonus_once(self):
        exam = self.make_exam()
        engine.on_exam_finished(self.user, exam)
        engine.on_exam_finished(self.user, exam)
        self.assertEqual(PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.EXAM_COMPLETED).count(), 1)

    def test_goal_reached_badge_and_daily_points_once(self):
        engine.set_goal(self.user, "daily_questions", 2)
        answer(self.user, "q-9-exp-001")
        self.assertNotIn("hedef-tamamlandi", badge_codes(self.user))
        rewards = answer(self.user, "q-9-exp-002")
        self.assertEqual(rewards.goals[0]["goal_type"], "daily_questions")
        self.assertIn("hedef-tamamlandi", [b["code"] for b in rewards.badges])
        answer(self.user, "q-9-exp-003")
        self.assertEqual(PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.GOAL_REACHED).count(), 1)


class TaskEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_tasks_assigned_once_per_period(self):
        engine.refresh_tasks(self.user)
        engine.refresh_tasks(self.user)
        self.assertEqual(DailyTask.objects.filter(user=self.user).count(), len(engine.TASK_TEMPLATES))

    def test_progress_counts_distinct_questions_and_rewards_once(self):
        task = next(t for t in engine.refresh_tasks(self.user) if t.task_type == "solve_questions")
        DailyTask.objects.filter(pk=task.pk).update(target=2)
        answer(self.user, "q-9-exp-001", correct=False)
        answer(self.user, "q-9-exp-001")  # aynı soru tekrar: ilerleme artmaz
        task.refresh_from_db()
        self.assertEqual((task.progress, task.completed_at), (1, None))
        rewards = answer(self.user, "q-9-exp-002")
        self.assertEqual([t["id"] for t in rewards.tasks], [task.pk])
        answer(self.user, "q-9-exp-003")
        entries = PointLedger.objects.filter(user=self.user, idempotency_key=f"task:{task.pk}")
        self.assertEqual(entries.count(), 1)

    def test_study_minutes_task(self):
        DailyStudyTotal.objects.create(user=self.user, date=timezone.localdate(), active_seconds=20 * 60)
        tasks = {t.task_type: t for t in engine.refresh_tasks(self.user)}
        self.assertIsNotNone(tasks["study_minutes"].completed_at)


class GoalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_changing_goal_closes_old_and_keeps_history(self):
        first = engine.set_goal(self.user, "daily_questions", 10)
        same = engine.set_goal(self.user, "daily_questions", 10)
        self.assertEqual(first.pk, same.pk)
        second = engine.set_goal(self.user, "daily_questions", 20)
        first.refresh_from_db()
        self.assertIsNotNone(first.valid_until)
        self.assertIsNone(second.valid_until)
        self.assertEqual(PersonalGoal.objects.filter(user=self.user).count(), 2)

    def test_history_uses_goal_valid_on_each_day(self):
        now = timezone.now()
        PersonalGoal.objects.create(
            user=self.user,
            goal_type="daily_questions",
            target=5,
            valid_from=now - timedelta(days=5),
            valid_until=now - timedelta(days=2),
        )
        PersonalGoal.objects.create(user=self.user, goal_type="daily_questions", target=30, valid_from=now)
        history = engine.goal_history(self.user, days=7)
        self.assertEqual(history[-1]["daily_questions"]["target"], 30)
        self.assertEqual(history[-4]["daily_questions"]["target"], 5)
        self.assertIsNone(history[0]["daily_questions"]["target"])


class GamificationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.client.force_authenticate(self.user)

    def test_summary(self):
        answer(self.user, "q-9-exp-001")
        data = self.client.get(reverse("gamification-summary")).data
        self.assertEqual(len(data["badges"]), 7)
        self.assertTrue(next(b for b in data["badges"] if b["code"] == "ilk-adim")["earned"])
        self.assertEqual(len(data["tasks"]), len(engine.TASK_TEMPLATES))
        ilk_adim = Badge.objects.get(code="ilk-adim").points_reward
        self.assertEqual(data["points"]["points"], engine.CORRECT_ANSWER_POINTS + ilk_adim)

    def test_put_goal_validates_range_and_returns_history(self):
        url = reverse("gamification-goals")
        bad = self.client.put(url, {"goal_type": "daily_questions", "target": 1}, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("target", bad.data["fields"])
        ok = self.client.put(url, {"goal_type": "daily_minutes", "target": 30}, format="json")
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        goal = next(g for g in ok.data["goals"] if g["goal_type"] == "daily_minutes")
        self.assertEqual(goal["target"], 30)
        self.assertEqual(len(ok.data["history"]), 14)

    def test_delete_goal_keeps_history(self):
        engine.set_goal(self.user, "daily_minutes", 30)
        response = self.client.delete(reverse("gamification-goal-detail", args=["daily_minutes"]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PersonalGoal.objects.filter(user=self.user, valid_until__isnull=True).exists())
        self.assertEqual(PersonalGoal.objects.filter(user=self.user).count(), 1)
