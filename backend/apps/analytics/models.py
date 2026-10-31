from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TopicProgress(models.Model):
    """Öğrencinin bir konudaki ilerlemesi. Konu kimlikleri content/ JSON'larından gelir."""

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Başlanmadı"
        IN_PROGRESS = "in_progress", "Devam ediyor"
        COMPLETED = "completed", "Tamamlandı"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_progress")
    grade = models.PositiveSmallIntegerField(validators=[MinValueValidator(9), MaxValueValidator(12)])
    topic_id = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NOT_STARTED)
    # "Son kalınan yer": konu anlatımındaki son görüntülenen bölüm (alt konu kimliği).
    last_section_id = models.CharField(max_length=64, blank=True)
    questions_answered = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "konu ilerlemesi"
        verbose_name_plural = "konu ilerlemeleri"
        constraints = [
            models.UniqueConstraint(fields=("user", "topic_id"), name="unique_topic_progress"),
            models.CheckConstraint(
                condition=models.Q(correct_answers__lte=models.F("questions_answered")),
                name="topic_progress_correct_lte_answered",
            ),
        ]
        indexes = [models.Index(fields=("user", "grade"))]

    def __str__(self):
        return f"{self.user} — {self.topic_id} ({self.get_status_display()})"

    @property
    def success_rate(self):
        """0–1 arası başarı oranı; hiç soru çözülmediyse None (tanı koymak için veri yok)."""
        if not self.questions_answered:
            return None
        return self.correct_answers / self.questions_answered


class MisconceptionLog(models.Model):
    """Öğrencinin yanlış şık seçimiyle ortaya çıkan kavram yanılgısı kaydı."""

    class Source(models.TextChoices):
        PRACTICE = "practice", "Soru çözümü"
        TIMED_EXAM = "timed_exam", "Süreli test"
        DIAGNOSTIC = "diagnostic", "Başlangıç seviye testi"
        REINFORCEMENT = "reinforcement", "Konu sonu pekiştirme"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="misconception_logs")
    question_id = models.CharField("soru", max_length=64)
    topic_id = models.CharField("konu", max_length=64)
    misconception_tag = models.CharField(max_length=96)
    subtopic_id = models.CharField("önerilen alt konu", max_length=64)
    selected_option = models.CharField(max_length=1)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.PRACTICE)
    created_at = models.DateTimeField("tarih", auto_now_add=True)

    class Meta:
        verbose_name = "kavram yanılgısı kaydı"
        verbose_name_plural = "kavram yanılgısı kayıtları"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("user", "misconception_tag")),
            models.Index(fields=("user", "created_at")),
            models.Index(fields=("user", "question_id")),
        ]

    def __str__(self):
        return f"{self.user} — {self.misconception_tag} ({self.question_id})"
