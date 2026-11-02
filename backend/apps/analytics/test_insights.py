"""Gelişim Haritası ve Hata Analizi testleri."""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import StudentProfile
from apps.curriculum.content_loader import get_repository

from .services import MIN_ANSWERS_FOR_DIAGNOSIS, MIN_REPEATS_FOR_PATTERN, error_analysis, mastery_level, mastery_map, record_attempt

User = get_user_model()


def wrong(question):
    return next(o for o in question.options if not o.is_correct)


def right(question):
    return next(o for o in question.options if o.is_correct)


def topic_item(data, topic_id):
    return next(t for theme in data["themes"] for t in theme["topics"] if t["id"] == topic_id)


class MasteryLevelTests(TestCase):
    def test_no_answers(self):
        self.assertEqual(mastery_level(0, None), "not_started")

    def test_few_answers_are_never_a_diagnosis(self):
        # 4 sorunun 4'ü de yanlış olsa bile kesin "tekrar et" tanısı konmaz.
        self.assertEqual(mastery_level(MIN_ANSWERS_FOR_DIAGNOSIS - 1, 0.0), "insufficient")
        self.assertEqual(mastery_level(MIN_ANSWERS_FOR_DIAGNOSIS - 1, 1.0), "insufficient")

    def test_levels_with_enough_data(self):
        n = MIN_ANSWERS_FOR_DIAGNOSIS
        self.assertEqual(mastery_level(n, 0.8), "mastered")
        self.assertEqual(mastery_level(n, 0.6), "developing")
        self.assertEqual(mastery_level(n, 0.2), "needs_review")


class MasteryMapTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.repo = get_repository()
        self.exp = self.repo.questions_for(topic_id="top-9-exp")

    def test_lists_every_topic_of_the_grade(self):
        data = mastery_map(self.user, 9)
        ids = {t["id"] for theme in data["themes"] for t in theme["topics"]}
        expected = {tid for tid, (g, _, _) in self.repo.topic_refs.items() if g == 9}
        self.assertEqual(ids, expected)
        self.assertEqual(data["levels"]["not_started"], len(expected))
        self.assertEqual(data["review"], [])

    def test_insufficient_data_is_reported_honestly(self):
        record_attempt(self.user, self.exp[0], wrong(self.exp[0]))
        item = topic_item(mastery_map(self.user, 9), "top-9-exp")
        self.assertEqual(item["level"], "insufficient")
        self.assertFalse(item["enough_data"])
        self.assertEqual(item["answers_needed"], MIN_ANSWERS_FOR_DIAGNOSIS - 1)
        # Düzeltilmemiş yanlışı olduğu için yine de tekrar listesinde görünür.
        self.assertTrue(item["needs_review"])
        self.assertEqual(item["open_mistakes"], 1)

    def test_needs_review_with_enough_data(self):
        for q in self.exp[:MIN_ANSWERS_FOR_DIAGNOSIS]:
            record_attempt(self.user, q, wrong(q))
        data = mastery_map(self.user, 9)
        item = topic_item(data, "top-9-exp")
        self.assertEqual(item["level"], "needs_review")
        self.assertEqual(data["review"][0]["id"], "top-9-exp")

    def test_mastered_topic_is_not_in_review(self):
        for q in self.exp[:MIN_ANSWERS_FOR_DIAGNOSIS]:
            record_attempt(self.user, q, right(q))
        data = mastery_map(self.user, 9)
        self.assertEqual(topic_item(data, "top-9-exp")["level"], "mastered")
        self.assertEqual(data["review"], [])

    def test_other_grades_are_excluded(self):
        record_attempt(self.user, self.exp[0], wrong(self.exp[0]))
        data = mastery_map(self.user, 10)
        self.assertTrue(all(t["questions_answered"] == 0 for theme in data["themes"] for t in theme["topics"]))


class ErrorAnalysisTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.q = get_repository().questions["q-9-exp-001"]
        self.option_b = next(o for o in self.q.options if o.key == "B")

    def test_single_occurrence_is_not_a_pattern_yet(self):
        record_attempt(self.user, self.q, self.option_b)
        data = error_analysis(self.user, 9)
        self.assertFalse(data["enough_data"])
        [pattern] = data["patterns"]
        self.assertEqual(pattern["tag"], "MISC_EXP_NEG_SIGN_CONFUSION")
        self.assertFalse(pattern["recurring"])
        self.assertEqual(pattern["recommended"]["section_id"], "top-9-exp-sign")
        self.assertTrue(pattern["detail"])

    def test_recurring_pattern(self):
        for _ in range(MIN_REPEATS_FOR_PATTERN):
            record_attempt(self.user, self.q, self.option_b)
        [pattern] = error_analysis(self.user, 9)["patterns"]
        self.assertTrue(pattern["recurring"])
        self.assertEqual(pattern["count"], MIN_REPEATS_FOR_PATTERN)
        self.assertEqual(pattern["question_count"], 1)

    def test_mistake_list_hides_answer_key(self):
        record_attempt(self.user, self.q, self.option_b)
        [mistake] = error_analysis(self.user, 9)["mistakes"]
        self.assertEqual(mistake["question_id"], self.q.id)
        self.assertEqual(mistake["selected_option"], "B")
        self.assertEqual(mistake["recommended"]["topic_id"], "top-9-exp")
        for forbidden in ("correct_option", "is_correct", "step_by_step_solution", "options"):
            self.assertNotIn(forbidden, mistake)

    def test_solving_correctly_later_resolves_mistake(self):
        record_attempt(self.user, self.q, self.option_b)
        record_attempt(self.user, self.q, right(self.q))
        data = error_analysis(self.user, 9)
        self.assertEqual(data["mistakes"], [])
        self.assertTrue(data["patterns"][0]["resolved"])
        self.assertEqual(data["totals"]["recurring_patterns"], 0)


class InsightsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        StudentProfile.objects.create(
            user=self.user, birth_date=date(2009, 5, 1), school_type=StudentProfile.SchoolType.ANADOLU, grade_level=10
        )
        self.client.force_authenticate(self.user)
        self.q = get_repository().questions["q-9-exp-001"]

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        for name in ("analytics-mastery-map", "analytics-error-analysis"):
            self.assertEqual(self.client.get(reverse(name)).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_defaults_to_profile_grade(self):
        response = self.client.get(reverse("analytics-mastery-map"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["grade"], 10)

    def test_invalid_grade(self):
        response = self.client.get(reverse("analytics-error-analysis"), {"grade": "8"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_own_data(self):
        other = User.objects.create_user(username="ayse", email="ayse@example.com", password="x")
        record_attempt(other, self.q, wrong(self.q))
        data = self.client.get(reverse("analytics-error-analysis"), {"grade": 9}).data
        self.assertEqual(data["patterns"], [])
        self.assertEqual(data["mistakes"], [])
        item = topic_item(self.client.get(reverse("analytics-mastery-map"), {"grade": 9}).data, "top-9-exp")
        self.assertEqual(item["questions_answered"], 0)
