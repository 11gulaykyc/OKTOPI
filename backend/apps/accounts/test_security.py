"""Yetkilendirme (IDOR) ve hata biçimi entegrasyon testleri.

Kural: hiçbir öğrenci başka bir öğrencinin test oturumuna, istatistiğine, hedefine veya profiline
erişemez. Kimlik içeren uç noktalarda başka kullanıcıya ait kayıt "yok" gibi davranır (404).
"""

import json
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import QuestionAttempt, TopicProgress
from apps.exams.models import ExamAnswer, PracticeSession, TimedExamSession
from apps.gamification import engine
from apps.gamification.models import PersonalGoal
from apps.study_sessions.models import StudySession

from .tests import make_student

PRIVATE_GET = (
    ("auth-me", ()),
    ("auth-diagnostic", ()),
    ("analytics-dashboard-summary", ()),
    ("analytics-topic-progress-list", ()),
    ("analytics-topic-progress", ("top-9-exp",)),
    ("exams-session-list", ()),
    ("exams-session-detail", ("practice", 1)),
    ("exams-session-result", ("timed", 1)),
    ("gamification-summary", ()),
    ("gamification-badges", ()),
    ("gamification-tasks", ()),
    ("gamification-goals", ()),
)
PRIVATE_POST = (
    ("auth-diagnostic", ()),
    ("analytics-topic-complete", ("top-9-exp",)),
    ("question-check", ("q-9-exp-001",)),
    ("exams-practice-start", ()),
    ("exams-timed-start", ()),
    ("exams-submit-answer", ()),
    ("exams-finish", ()),
    ("study-heartbeat", ()),
)


class AuthenticationRequiredTests(APITestCase):
    def test_private_endpoints_reject_anonymous_with_turkish_message(self):
        for name, args in PRIVATE_GET:
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, name)
            self.assertEqual(response.data["code"], "not_authenticated", name)
            self.assertIn("giriş", response.data["detail"], name)
        for name, args in PRIVATE_POST:
            response = self.client.post(reverse(name, args=args), {}, format="json")
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, name)

    def test_invalid_token_hides_token_details(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer bozuk-token")
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(set(response.data), {"detail", "code"})
        self.assertEqual(response.data["code"], "token_not_valid")


class CrossUserAccessTests(APITestCase):
    """Ayşe'nin kayıtları oluşturulur; Mehmet aynı kimliklerle erişmeye çalışır."""

    def setUp(self):
        self.owner = make_student(username="ayse", email="ayse@example.com", grade=9)
        self.attacker = make_student(username="mehmet", email="mehmet@example.com", grade=9)
        self.client.force_authenticate(self.owner)
        self.practice = self.client.post(
            reverse("exams-practice-start"), {"grade": 9, "topic_id": "top-9-exp", "count": 3}, format="json"
        ).data
        self.timed = self.client.post(
            reverse("exams-timed-start"), {"grade": 9, "topic_id": "top-9-exp", "count": 3}, format="json"
        ).data
        qid = self.timed["questions"][0]["id"]
        self.client.post(
            reverse("exams-submit-answer"),
            {"session_type": "timed", "session_id": self.timed["id"], "question_id": qid, "selected_option": "A"},
            format="json",
        )
        self.client.post(reverse("analytics-topic-complete", args=["top-9-exp"]))
        engine.set_goal(self.owner, "daily_questions", 10)
        self.client.post(reverse("study-heartbeat"), {}, format="json")
        self.client.force_authenticate(self.attacker)

    def test_cannot_read_other_students_sessions_or_results(self):
        for kind, session in (("practice", self.practice), ("timed", self.timed)):
            for name in ("exams-session-detail", "exams-session-result"):
                response = self.client.get(reverse(name, args=[kind, session["id"]]))
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, (name, kind))
                self.assertNotIn("questions", response.data)
        self.assertEqual(self.client.get(reverse("exams-session-list")).data, [])

    def test_cannot_answer_or_finish_other_students_exam(self):
        qid = self.timed["questions"][1]["id"]
        submit = self.client.post(
            reverse("exams-submit-answer"),
            {"session_type": "timed", "session_id": self.timed["id"], "question_id": qid, "selected_option": "B"},
            format="json",
        )
        finish = self.client.post(
            reverse("exams-finish"), {"session_type": "timed", "session_id": self.timed["id"]}, format="json"
        )
        practice_submit = self.client.post(
            reverse("exams-submit-answer"),
            {"session_type": "practice", "session_id": self.practice["id"], "question_id": self.practice["questions"][0]["id"], "selected_option": "A"},
            format="json",
        )
        for response in (submit, finish, practice_submit):
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Ayşe'nin testi değişmedi.
        self.assertIsNone(TimedExamSession.objects.get(pk=self.timed["id"]).finished_at)
        self.assertEqual(ExamAnswer.objects.filter(timed_session_id=self.timed["id"]).count(), 1)
        self.assertFalse(ExamAnswer.objects.filter(practice_session_id=self.practice["id"]).exists())
        self.assertFalse(QuestionAttempt.objects.filter(user=self.attacker).exists())

    def test_statistics_progress_and_goals_are_isolated(self):
        summary = self.client.get(reverse("analytics-dashboard-summary")).data
        self.assertEqual(summary["topics"]["completed"], 0)
        self.assertEqual(summary["points"]["points"], 0)
        self.assertEqual(summary["goals"], [])
        self.assertEqual(self.client.get(reverse("analytics-topic-progress-list")).data, [])
        self.assertEqual(self.client.get(reverse("analytics-topic-progress", args=["top-9-exp"])).data["status"], "not_started")
        gamification = self.client.get(reverse("gamification-summary")).data
        self.assertEqual(gamification["points"]["points"], 0)
        self.assertFalse(any(b["earned"] for b in gamification["badges"]))
        self.assertTrue(all(g["target"] is None for g in gamification["goals"]))

    def test_goal_changes_only_affect_own_goals(self):
        self.client.put(reverse("gamification-goals"), {"goal_type": "daily_questions", "target": 50}, format="json")
        self.client.delete(reverse("gamification-goal-detail", args=["daily_questions"]))
        owner_goal = PersonalGoal.objects.get(user=self.owner, valid_until__isnull=True)
        self.assertEqual(owner_goal.target, 10)

    def test_profile_endpoint_never_exposes_or_edits_other_users(self):
        me = self.client.get(reverse("auth-me")).data
        self.assertEqual(me["username"], "mehmet")
        # Gövdeye başka kullanıcının kimliği yazılsa da yalnızca oturumdaki kullanıcı güncellenir.
        self.client.patch(reverse("auth-me"), {"id": self.owner.id, "username": "ayse", "first_name": "Mehmet"}, format="json")
        self.owner.refresh_from_db()
        self.assertNotEqual(self.owner.first_name, "Mehmet")
        self.assertEqual(self.client.get(reverse("auth-me")).data["username"], "mehmet")

    def test_heartbeat_only_touches_own_session(self):
        owner_session = StudySession.objects.get(user=self.owner)
        before = (owner_session.heartbeat_count, owner_session.last_heartbeat_at)
        self.client.post(reverse("study-heartbeat"), {}, format="json")
        owner_session.refresh_from_db()
        self.assertEqual((owner_session.heartbeat_count, owner_session.last_heartbeat_at), before)
        self.assertTrue(StudySession.objects.filter(user=self.attacker).exists())

    def test_session_ids_are_not_enumerable(self):
        """Sıralı kimliklerin tamamı denense de yalnızca kendi oturumları görünür."""
        last_id = max(PracticeSession.objects.order_by("-pk").first().pk, TimedExamSession.objects.order_by("-pk").first().pk)
        for kind in ("practice", "timed"):
            for pk in range(1, last_id + 1):
                response = self.client.get(reverse("exams-session-detail", args=[kind, pk]))
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_topic_progress_of_owner_unchanged_by_attacker(self):
        self.client.patch(reverse("analytics-topic-progress", args=["top-9-exp"]), {"last_section_id": "top-9-exp-neg"}, format="json")
        owner_progress = TopicProgress.objects.get(user=self.owner, topic_id="top-9-exp")
        self.assertEqual(owner_progress.status, "completed")
        self.assertEqual(owner_progress.last_section_id, "")


class ErrorFormatTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(make_student())

    def test_validation_error_shape(self):
        response = self.client.post(reverse("exams-practice-start"), {"grade": 15}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "invalid")
        self.assertIn("grade", response.data["fields"])
        self.assertEqual(response.data["detail"], str(response.data["fields"]["grade"][0]))

    def test_non_field_validation_error_has_no_fields(self):
        response = self.client.post(reverse("exams-practice-start"), {"grade": 12}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("fields", response.data)
        self.assertIn("soru bulunamadı", response.data["detail"])

    def test_not_found_and_method_not_allowed_are_turkish(self):
        not_found = self.client.get(reverse("exams-session-detail", args=["practice", 999]))
        self.assertEqual(not_found.data, {"detail": "Oturum bulunamadı.", "code": "not_found"})
        not_allowed = self.client.delete(reverse("auth-me"))
        self.assertEqual(not_allowed.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(not_allowed.data["code"], "method_not_allowed")

    @override_settings(DEBUG=False)
    def test_unexpected_errors_hide_technical_details(self):
        with mock.patch("apps.analytics.views.dashboard_summary", side_effect=RuntimeError("SQL: SELECT * gizli")):
            with self.assertLogs("oktopi.api", level="ERROR"):
                response = self.client.get(reverse("analytics-dashboard-summary"))
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["code"], "server_error")
        self.assertNotIn("SQL", json.dumps(response.data))
