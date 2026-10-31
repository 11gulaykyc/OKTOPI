from django.conf import settings
from django.db import models


class StudySession(models.Model):
    """Kesintisiz bir aktif çalışma dönemi. 2 dakikadan uzun sessizlik oturumu kapatır."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_sessions")
    started_at = models.DateTimeField("başlangıç")
    last_heartbeat_at = models.DateTimeField("son heartbeat")
    active_seconds = models.PositiveIntegerField("toplam aktif saniye", default=0)
    heartbeat_count = models.PositiveIntegerField(default=1)
    ended_at = models.DateTimeField("bitiş", null=True, blank=True)
    # Son heartbeat'in geldiği bağlam, ör. "topic:top-9-exp" veya "exam:42".
    context = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "çalışma oturumu"
        verbose_name_plural = "çalışma oturumları"
        ordering = ("-started_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=models.Q(ended_at__isnull=True),
                name="one_open_study_session_per_user",
            ),
        ]
        indexes = [models.Index(fields=("user", "started_at"))]

    def __str__(self):
        return f"{self.user} — {self.started_at:%Y-%m-%d %H:%M} ({self.active_seconds} sn)"

    @property
    def is_open(self):
        return self.ended_at is None


class DailyStudyTotal(models.Model):
    """Gün bazında aktif çalışma süresi (Europe/Istanbul tarihine göre). Panel istatistikleri buradan okunur."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_study_totals")
    date = models.DateField()
    active_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "günlük çalışma süresi"
        verbose_name_plural = "günlük çalışma süreleri"
        constraints = [models.UniqueConstraint(fields=("user", "date"), name="unique_daily_study_total")]
        ordering = ("-date",)

    def __str__(self):
        return f"{self.user} — {self.date}: {self.active_seconds} sn"
