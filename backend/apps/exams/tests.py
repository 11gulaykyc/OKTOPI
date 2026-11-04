import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import MisconceptionLog, QuestionAttempt
from apps.curriculum.content_loader import get_repository
from apps.gamification.engine import CORRECT_ANSWER_POINTS
from apps.gamification.models import PointLedger

from .models import ExamAnswer, PracticeSession, TimedExamSession
from .services import DEADLINE_GRACE

User = get_user_model()


def correct_key(question_id):
    return get_repository().questions[question_id].correct_option.key


def wrong_key(question_id):
    return next(o.key for o in get_repository().questions[question_id].options if not o.is_correct)


class ExamApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")
        self.client.force_authenticate(self.user)

    def start(self, kind, **payload):
        return self.client.post(reverse(f"exams-{kind}-start"), {"grade": 9, **payload}, format="json")

    def submit(self, kind, session_id, question_id, option):
        return self.client.post(
            reverse("exams-submit-answer"),
            {"session_type": kind, "session_id": session_id, "question_id": question_id, "selected_option": option},
            format="json",
        )

    def finish(self, kind, session_id):
        return self.client.post(reverse("exams-finish"), {"session_type": kind, "session_id": session_id}, format="json")


class PracticeSessionTests(ExamApiTestCase):
    def test_start_returns_questions_without_answer_key(self):
        response = self.start("practice", topic_id="top-9-exp", count=5)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["question_count"], 5)
        self.assertTrue(all(q["topic_id"] == "top-9-exp" for q in response.data["questions"]))
        body = json.dumps(response.data, default=str)
        for secret in ("is_correct", "misconception_tag", "step_by_step_solution", "correct_option"):
            self.assertNotIn(secret, body)

    def test_unknown_or_foreign_topic_rejected(self):
        self.assertEqual(self.start("practice", topic_id="top-9-yok").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.start("practice", grade=10, topic_id="top-9-exp").status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_questions_for_selection(self):
        response = self.start("practice", grade=12)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("soru bulunamadı", response.data["detail"])

    def test_wrong_answer_returns_solution_and_logs_misconception(self):
        session = self.start("practice", topic_id="top-9-exp", count=3).data
        qid = session["questions"][0]["id"]
        response = self.submit("practice", session["id"], qid, wrong_key(qid))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_correct"])
        self.assertEqual(response.data["correct_option"], correct_key(qid))
        self.assertTrue(response.data["step_by_step_solution"])
        self.assertIsNotNone(response.data["misconception"]["recommended"])
        log = MisconceptionLog.objects.get(user=self.user)
        self.assertEqual((log.question_id, log.source), (qid, MisconceptionLog.Source.PRACTICE))
        self.assertEqual(ExamAnswer.objects.get(practice_session_id=session["id"]).selected_option, wrong_key(qid))

    def test_second_answer_to_same_question_rejected(self):
        session = self.start("practice", topic_id="top-9-exp", count=2).data
        qid = session["questions"][0]["id"]
        self.submit("practice", session["id"], qid, wrong_key(qid))
        response = self.submit("practice", session["id"], qid, correct_key(qid))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(QuestionAttempt.objects.filter(user=self.user).count(), 1)

    def test_question_outside_session_rejected(self):
        session = self.start("practice", topic_id="top-9-exp", count=1).data
        response = self.submit("practice", session["id"], "q-9-tri-001", "A")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("question_id", response.data["fields"])

    def test_correct_answer_points_are_awarded_once_per_question_for_life(self):
        qid = "q-9-exp-001"
        for _ in range(2):
            session = self.start("practice", topic_id="top-9-exp", count=7).data
            self.submit("practice", session["id"], qid, correct_key(qid))
        entries = PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.CORRECT_ANSWER)
        self.assertEqual(list(entries.values_list("amount", flat=True)), [CORRECT_ANSWER_POINTS])

    def test_state_restores_revealed_answers_and_finish_counts(self):
        session = self.start("practice", topic_id="top-9-exp", count=3).data
        q1, q2, _ = (q["id"] for q in session["questions"])
        self.submit("practice", session["id"], q1, correct_key(q1))
        self.submit("practice", session["id"], q2, wrong_key(q2))
        state = self.client.get(reverse("exams-session-detail", args=["practice", session["id"]])).data
        self.assertEqual(set(state["answers"]), {q1, q2})
        self.assertTrue(state["answers"][q1]["is_correct"])

        result = self.finish("practice", session["id"]).data
        self.assertEqual(
            {k: result["summary"][k] for k in ("correct", "incorrect", "blank")}, {"correct": 1, "incorrect": 1, "blank": 1}
        )
        self.assertEqual(len(result["misconceptions"]), 1)
        self.assertGreater(result["rewards"]["points"], 0)
        self.assertEqual(self.submit("practice", session["id"], _, "A").status_code, status.HTTP_409_CONFLICT)

    def test_mistakes_only_mode_uses_open_mistakes(self):
        session = self.start("practice", topic_id="top-9-exp", count=7).data
        qids = [q["id"] for q in session["questions"]]
        self.submit("practice", session["id"], qids[0], wrong_key(qids[0]))
        self.submit("practice", session["id"], qids[1], wrong_key(qids[1]))
        self.submit("practice", session["id"], qids[2], correct_key(qids[2]))
        retry = self.start("practice", mistakes_only=True).data
        self.assertEqual({q["id"] for q in retry["questions"]}, {qids[0], qids[1]})
        # Hata doğru çözülünce listeden çıkar.
        self.submit("practice", retry["id"], qids[0], correct_key(qids[0]))
        again = self.start("practice", mistakes_only=True).data
        self.assertEqual([q["id"] for q in again["questions"]], [qids[1]])

    def test_mistakes_only_without_mistakes(self):
        response = self.start("practice", mistakes_only=True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TimedExamTests(ExamApiTestCase):
    def test_start_sets_server_side_deadline(self):
        response = self.start("timed", topic_id="top-9-exp", count=4)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session = TimedExamSession.objects.get(pk=response.data["id"])
        self.assertEqual(session.duration_seconds, 6 * 60)  # 4 soru x 90 sn
        self.assertEqual(session.deadline, session.started_at + timedelta(seconds=session.duration_seconds))
        self.assertGreater(response.data["remaining_seconds"], 350)

    def test_custom_duration(self):
        response = self.start("timed", count=3, duration_minutes=10)
        self.assertEqual(response.data["duration_seconds"], 600)
        self.assertEqual(self.start("timed", duration_minutes=0).status_code, status.HTTP_400_BAD_REQUEST)

    def test_answers_reveal_nothing_until_finished_and_can_change(self):
        session = self.start("timed", topic_id="top-9-exp", count=3).data
        qid = session["questions"][0]["id"]
        first = self.submit("timed", session["id"], qid, wrong_key(qid))
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(set(first.data), {"question_id", "selected_option", "answered_count", "remaining_seconds"})
        self.submit("timed", session["id"], qid, correct_key(qid))
        self.assertEqual(ExamAnswer.objects.get(timed_session_id=session["id"]).selected_option, correct_key(qid))
        # Henüz istatistik/yanılgı yazılmaz; sonuç istenemez.
        self.assertFalse(QuestionAttempt.objects.exists())
        result = self.client.get(reverse("exams-session-result", args=["timed", session["id"]]))
        self.assertEqual(result.status_code, status.HTTP_409_CONFLICT)
        state = self.client.get(reverse("exams-session-detail", args=["timed", session["id"]])).data
        self.assertEqual(state["answers"], {qid: correct_key(qid)})
        self.assertNotIn("is_correct", json.dumps(state, default=str))

    def test_clearing_answer_makes_it_blank(self):
        session = self.start("timed", topic_id="top-9-exp", count=2).data
        qid = session["questions"][0]["id"]
        self.submit("timed", session["id"], qid, "A")
        response = self.submit("timed", session["id"], qid, None)
        self.assertEqual(response.data["answered_count"], 0)

    def test_finish_evaluates_logs_and_is_idempotent(self):
        session = self.start("timed", topic_id="top-9-exp", count=3).data
        q1, q2, q3 = (q["id"] for q in session["questions"])
        self.submit("timed", session["id"], q1, correct_key(q1))
        self.submit("timed", session["id"], q2, wrong_key(q2))
        first = self.finish("timed", session["id"])
        second = self.finish("timed", session["id"])
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {k: first.data["summary"][k] for k in ("correct", "incorrect", "blank")}, {"correct": 1, "incorrect": 1, "blank": 1}
        )
        self.assertFalse(first.data["auto_finished"])
        items = {i["question_id"]: i for i in first.data["items"]}
        self.assertEqual(items[q2]["correct_option"], correct_key(q2))
        self.assertFalse(items[q3]["answered"])
        # Kayıtlar yalnızca bir kez yazılır.
        self.assertEqual(QuestionAttempt.objects.filter(user=self.user, source="timed_exam").count(), 3)
        self.assertEqual(MisconceptionLog.objects.filter(user=self.user, source="timed_exam").count(), 1)
        self.assertEqual(second.data["summary"], first.data["summary"])
        self.assertEqual(PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.EXAM_COMPLETED).count(), 1)
        self.assertEqual(self.submit("timed", session["id"], q3, "A").status_code, status.HTTP_409_CONFLICT)

    def test_exam_bonus_requires_half_answered(self):
        session = self.start("timed", topic_id="top-9-exp", count=4).data
        qid = session["questions"][0]["id"]
        self.submit("timed", session["id"], qid, correct_key(qid))
        self.finish("timed", session["id"])
        self.assertFalse(PointLedger.objects.filter(user=self.user, reason=PointLedger.Reason.EXAM_COMPLETED).exists())

    def expire(self, session_id):
        TimedExamSession.objects.filter(pk=session_id).update(
            deadline=timezone.now() - DEADLINE_GRACE - timedelta(seconds=1)
        )

    def test_answer_after_deadline_rejected_and_exam_auto_finished(self):
        session = self.start("timed", topic_id="top-9-exp", count=2).data
        qid = session["questions"][0]["id"]
        self.submit("timed", session["id"], qid, correct_key(qid))
        self.expire(session["id"])
        late = self.submit("timed", session["id"], session["questions"][1]["id"], "A")
        self.assertEqual(late.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(late.data["code"], "time_up")
        exam = TimedExamSession.objects.get(pk=session["id"])
        self.assertTrue(exam.auto_finished)
        self.assertEqual((exam.correct_count, exam.blank_count), (1, 1))
        self.assertLessEqual(exam.finished_at, exam.deadline)

    def test_viewing_expired_exam_finishes_it(self):
        session = self.start("timed", count=2).data
        self.expire(session["id"])
        state = self.client.get(reverse("exams-session-detail", args=["timed", session["id"]])).data
        self.assertTrue(state["is_finished"])
        self.assertTrue(state["auto_finished"])
        self.assertEqual(state["remaining_seconds"], 0)

    def test_answer_within_grace_period_is_accepted(self):
        session = self.start("timed", count=1).data
        TimedExamSession.objects.filter(pk=session["id"]).update(deadline=timezone.now() - timedelta(seconds=2))
        qid = session["questions"][0]["id"]
        self.assertEqual(self.submit("timed", session["id"], qid, "A").status_code, status.HTTP_200_OK)

    def test_session_list_shows_own_sessions(self):
        self.start("practice", count=1)
        self.start("timed", count=1)
        data = self.client.get(reverse("exams-session-list")).data
        self.assertEqual(sorted(s["type"] for s in data), ["practice", "timed"])


class ExamRequiresAuthTests(APITestCase):
    def test_endpoints_require_login(self):
        for name in ("exams-practice-start", "exams-timed-start", "exams-submit-answer", "exams-finish"):
            self.assertEqual(self.client.post(reverse(name), {}, format="json").status_code, status.HTTP_401_UNAUTHORIZED)


class RandomSelectionTests(ExamApiTestCase):
    def test_count_is_capped_by_pool(self):
        with mock.patch("apps.exams.services.random.sample", side_effect=lambda pool, k: list(pool)[:k]):
            data = self.start("practice", topic_id="top-9-tri", count=30).data
        self.assertEqual(data["question_count"], len(get_repository().questions_for(topic_id="top-9-tri")))
        self.assertEqual(PracticeSession.objects.get(pk=data["id"]).question_count, data["question_count"])
