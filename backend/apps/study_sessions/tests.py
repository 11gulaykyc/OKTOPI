from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DailyStudyTotal, StudySession
from .services import end_session, record_heartbeat

User = get_user_model()
T0 = datetime(2026, 10, 31, 14, 0, 0, tzinfo=ZoneInfo("Europe/Istanbul"))


def at(seconds):
    return T0 + timedelta(seconds=seconds)


class HeartbeatServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_first_heartbeat_starts_session_with_zero_seconds(self):
        result = record_heartbeat(self.user, now=at(0))
        self.assertTrue(result.new_session)
        self.assertEqual(result.session.active_seconds, 0)
        self.assertEqual(result.session.started_at, at(0))

    def test_regular_heartbeats_accumulate(self):
        for t in (0, 60, 120, 180):
            result = record_heartbeat(self.user, now=at(t))
        self.assertEqual(result.session.active_seconds, 180)
        self.assertEqual(StudySession.objects.count(), 1)
        self.assertEqual(DailyStudyTotal.objects.get(user=self.user).active_seconds, 180)

    def test_rapid_pings_cannot_exceed_real_elapsed_time(self):
        record_heartbeat(self.user, now=at(0))
        for t in range(1, 31):  # 30 ping, saniyede bir
            result = record_heartbeat(self.user, now=at(t))
        self.assertEqual(result.session.active_seconds, 30)

    def test_late_heartbeat_within_timeout_is_capped_to_interval(self):
        record_heartbeat(self.user, now=at(0))
        result = record_heartbeat(self.user, now=at(110))
        self.assertFalse(result.new_session)
        self.assertEqual(result.credited_seconds, 60)

    def test_idle_over_two_minutes_freezes_session_and_starts_new(self):
        record_heartbeat(self.user, now=at(0))
        record_heartbeat(self.user, now=at(60))
        result = record_heartbeat(self.user, now=at(60 + 121))

        self.assertTrue(result.new_session)
        self.assertEqual(result.credited_seconds, 0)
        old = StudySession.objects.exclude(pk=result.session.pk).get()
        self.assertEqual(old.active_seconds, 60)
        self.assertEqual(old.ended_at, at(60))  # son heartbeat anında dondurulur
        self.assertEqual(DailyStudyTotal.objects.get(user=self.user).active_seconds, 60)

    def test_tab_left_open_for_hours_adds_nothing(self):
        record_heartbeat(self.user, now=at(0))
        record_heartbeat(self.user, now=at(60))
        record_heartbeat(self.user, now=at(3 * 3600))
        total = sum(s.active_seconds for s in StudySession.objects.all())
        self.assertEqual(total, 60)

    def test_exactly_at_timeout_still_counts(self):
        record_heartbeat(self.user, now=at(0))
        result = record_heartbeat(self.user, now=at(120))
        self.assertFalse(result.new_session)
        self.assertEqual(result.credited_seconds, 60)

    def test_clock_going_backwards_credits_nothing(self):
        record_heartbeat(self.user, now=at(100))
        result = record_heartbeat(self.user, now=at(90))
        self.assertEqual(result.credited_seconds, 0)
        self.assertEqual(result.session.last_heartbeat_at, at(100))

    def test_sessions_are_per_user(self):
        other = User.objects.create_user(username="veli", email="veli@example.com", password="x")
        record_heartbeat(self.user, now=at(0))
        record_heartbeat(other, now=at(30))
        record_heartbeat(self.user, now=at(60))
        self.assertEqual(StudySession.objects.get(user=self.user).active_seconds, 60)
        self.assertEqual(StudySession.objects.get(user=other).active_seconds, 0)

    def test_daily_totals_split_by_local_date(self):
        midnight = datetime(2026, 11, 1, 0, 0, 0, tzinfo=ZoneInfo("Europe/Istanbul"))
        record_heartbeat(self.user, now=midnight - timedelta(seconds=60))
        record_heartbeat(self.user, now=midnight - timedelta(seconds=10))
        record_heartbeat(self.user, now=midnight + timedelta(seconds=50))
        totals = {d.date.isoformat(): d.active_seconds for d in DailyStudyTotal.objects.all()}
        self.assertEqual(totals, {"2026-10-31": 50, "2026-11-01": 60})

    def test_end_session_closes_at_last_heartbeat(self):
        record_heartbeat(self.user, now=at(0))
        record_heartbeat(self.user, now=at(60))
        session = end_session(self.user, now=at(90))
        self.assertEqual(session.ended_at, at(60))
        self.assertTrue(record_heartbeat(self.user, now=at(100)).new_session)


class HeartbeatApiTests(APITestCase):
    url = reverse("study-heartbeat")

    def setUp(self):
        self.user = User.objects.create_user(username="ali", email="ali@example.com", password="x")

    def test_requires_authentication(self):
        self.assertEqual(self.client.post(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_heartbeat_flow_uses_server_clock(self):
        self.client.force_authenticate(self.user)
        with mock.patch("django.utils.timezone.now", return_value=at(0)):
            first = self.client.post(self.url, {"context": "topic:top-9-exp"}, format="json")
        with mock.patch("django.utils.timezone.now", return_value=at(60)):
            second = self.client.post(self.url, {}, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertTrue(first.data["new_session"])
        self.assertEqual(second.data["session_id"], first.data["session_id"])
        self.assertEqual(second.data["credited_seconds"], 60)
        self.assertEqual(second.data["today_active_seconds"], 60)
        self.assertEqual(StudySession.objects.get().context, "topic:top-9-exp")

    def test_client_cannot_send_duration(self):
        self.client.force_authenticate(self.user)
        with mock.patch("django.utils.timezone.now", return_value=at(0)):
            self.client.post(self.url, {}, format="json")
        with mock.patch("django.utils.timezone.now", return_value=at(5)):
            response = self.client.post(self.url, {"active_seconds": 99999, "credited_seconds": 99999}, format="json")
        self.assertEqual(response.data["session_active_seconds"], 5)

    def test_heartbeat_returns_study_time_rewards(self):
        """Süreyle ulaşılan hedef/rozet heartbeat yanıtında döner (istemci bunu bildirim olarak gösterir)."""
        from apps.gamification.models import PersonalGoal

        self.client.force_authenticate(self.user)
        PersonalGoal.objects.create(user=self.user, goal_type="daily_minutes", target=10, valid_from=at(-3600))
        DailyStudyTotal.objects.create(user=self.user, date=at(0).astimezone(ZoneInfo("Europe/Istanbul")).date(), active_seconds=570)
        with mock.patch("django.utils.timezone.now", return_value=at(0)):
            first = self.client.post(self.url, {}, format="json")
        with mock.patch("django.utils.timezone.now", return_value=at(60)):
            second = self.client.post(self.url, {}, format="json")
        self.assertEqual(first.data["rewards"]["goals"], [])
        self.assertEqual(second.data["rewards"]["goals"][0]["goal_type"], "daily_minutes")
        self.assertEqual([b["code"] for b in second.data["rewards"]["badges"]], ["hedef-tamamlandi"])

    def test_end_endpoint(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(reverse("study-end")).status_code, status.HTTP_204_NO_CONTENT)
        self.client.post(self.url, {}, format="json")
        self.assertEqual(self.client.post(reverse("study-end")).status_code, status.HTTP_200_OK)
