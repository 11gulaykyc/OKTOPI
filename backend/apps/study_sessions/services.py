from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import DailyStudyTotal, StudySession


@dataclass
class HeartbeatResult:
    session: StudySession
    credited_seconds: int
    new_session: bool


def _close_stale_sessions(user, now, idle_timeout):
    """Son heartbeat'i zaman aşımını geçmiş açık oturumları, son heartbeat anında kapatır."""
    cutoff = now - idle_timeout
    StudySession.objects.filter(user=user, ended_at__isnull=True, last_heartbeat_at__lt=cutoff).update(
        ended_at=F("last_heartbeat_at")
    )


def record_heartbeat(user, now=None, context=""):
    """Bir heartbeat işler ve aktif süreyi sunucu saatine göre kredilendirir.

    - İlk heartbeat yeni oturum başlatır (0 sn).
    - Önceki heartbeat'ten bu yana geçen süre zaman aşımını (120 sn) geçmediyse,
      en fazla bir heartbeat aralığı (60 sn) kadar süre eklenir. Böylece sık ping
      atılsa da gerçek geçen süreden fazlası yazılamaz, seyrek ping'lerde de
      arada geçen belirsiz süre şişirilmez.
    - Zaman aşımı geçtiyse eski oturum son heartbeat anında dondurulur ve yeni oturum açılır.
    """
    now = now or timezone.now()
    interval = settings.HEARTBEAT_INTERVAL_SECONDS
    idle_timeout = timedelta(seconds=settings.HEARTBEAT_IDLE_TIMEOUT_SECONDS)
    context = (context or "")[:100]

    with transaction.atomic():
        _close_stale_sessions(user, now, idle_timeout)
        session = StudySession.objects.select_for_update().filter(user=user, ended_at__isnull=True).first()

        if session is None:
            try:
                with transaction.atomic():
                    session = StudySession.objects.create(
                        user=user, started_at=now, last_heartbeat_at=now, context=context
                    )
            except IntegrityError:
                # Eşzamanlı başka bir istek oturumu az önce açtı; onu kullan.
                session = StudySession.objects.select_for_update().get(user=user, ended_at__isnull=True)
            else:
                return HeartbeatResult(session=session, credited_seconds=0, new_session=True)

        elapsed = (now - session.last_heartbeat_at).total_seconds()
        credited = int(max(0, min(elapsed, interval)))
        if elapsed > 0:
            session.last_heartbeat_at = now
        session.active_seconds += credited
        session.heartbeat_count += 1
        if context:
            session.context = context
        session.save(update_fields=["last_heartbeat_at", "active_seconds", "heartbeat_count", "context"])

        if credited:
            day = timezone.localdate(now)
            total, _ = DailyStudyTotal.objects.get_or_create(user=user, date=day)
            DailyStudyTotal.objects.filter(pk=total.pk).update(active_seconds=F("active_seconds") + credited)

    return HeartbeatResult(session=session, credited_seconds=credited, new_session=False)


def end_session(user, now=None):
    """Açık oturumu kapatır (ör. çıkış yaparken). Son heartbeat'ten sonrası sayılmaz."""
    now = now or timezone.now()
    with transaction.atomic():
        session = StudySession.objects.select_for_update().filter(user=user, ended_at__isnull=True).first()
        if session is None:
            return None
        session.ended_at = session.last_heartbeat_at
        session.save(update_fields=["ended_at"])
        return session
