from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.curriculum.content_loader import get_repository

from .models import MisconceptionLog, TopicProgress
from .services import log_misconception

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
