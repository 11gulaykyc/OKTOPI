from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from .models import Badge, PersonalGoal, PointLedger, UserBadge
from .services import award_points, total_points

User = get_user_model()


class PointLedgerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_same_idempotency_key_awards_once(self):
        _, created_first = award_points(self.user, 50, PointLedger.Reason.EXAM_COMPLETED, "exam:1:finish")
        _, created_second = award_points(self.user, 50, PointLedger.Reason.EXAM_COMPLETED, "exam:1:finish")
        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(total_points(self.user), 50)

    def test_different_keys_accumulate(self):
        award_points(self.user, 10, PointLedger.Reason.CORRECT_ANSWER, "answer:1")
        award_points(self.user, 10, PointLedger.Reason.CORRECT_ANSWER, "answer:2")
        self.assertEqual(total_points(self.user), 20)

    def test_same_key_different_users_is_allowed(self):
        other = User.objects.create_user(username="veli", email="veli@example.com", password="x")
        award_points(self.user, 10, PointLedger.Reason.CORRECT_ANSWER, "answer:1")
        award_points(other, 10, PointLedger.Reason.CORRECT_ANSWER, "answer:1")
        self.assertEqual(total_points(other), 10)


class BadgeAndGoalConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_badge_awarded_once(self):
        badge = Badge.objects.create(code="ilk-adim", name="İlk Adım", description="İlk soruyu çöz")
        UserBadge.objects.create(user=self.user, badge=badge)
        with self.assertRaises(IntegrityError):
            UserBadge.objects.create(user=self.user, badge=badge)

    def test_only_one_active_goal_per_type(self):
        now = timezone.now()
        PersonalGoal.objects.create(user=self.user, goal_type="daily_questions", target=10, valid_from=now)
        with self.assertRaises(IntegrityError):
            PersonalGoal.objects.create(user=self.user, goal_type="daily_questions", target=20, valid_from=now)

    def test_closed_goal_keeps_history(self):
        now = timezone.now()
        old = PersonalGoal.objects.create(user=self.user, goal_type="daily_questions", target=10, valid_from=now)
        old.valid_until = now
        old.save()
        PersonalGoal.objects.create(user=self.user, goal_type="daily_questions", target=20, valid_from=now)
        self.assertEqual(PersonalGoal.objects.filter(user=self.user).count(), 2)
