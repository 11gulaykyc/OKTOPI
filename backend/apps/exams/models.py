from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class BaseExamSession(models.Model):
    """Soru çözümü ve süreli test oturumlarının ortak alanları.

    Sorular content/ JSON'larından gelir; oturum yalnızca soru kimliklerini (sabit sırayla) saklar.
    Sayaçlar (doğru/yanlış/boş) oturum bitirilirken sunucuda hesaplanıp yazılır.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(class)ss")
    grade = models.PositiveSmallIntegerField(validators=[MinValueValidator(9), MaxValueValidator(12)])
    topic_id = models.CharField("konu filtresi", max_length=64, blank=True)
    question_ids = models.JSONField(default=list)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    correct_count = models.PositiveSmallIntegerField(default=0)
    incorrect_count = models.PositiveSmallIntegerField(default=0)
    blank_count = models.PositiveSmallIntegerField(default=0)
    # Bitişte kazanılan ödüller (puan, rozet, görev); sonuç ekranında tekrar gösterilebilsin diye saklanır.
    rewards = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        ordering = ("-started_at",)

    @property
    def is_finished(self):
        return self.finished_at is not None

    @property
    def question_count(self):
        return len(self.question_ids)

    @property
    def answered_count(self):
        return self.correct_count + self.incorrect_count


class PracticeSession(BaseExamSession):
    """Süresiz soru çözümü: her cevabın ardından doğru şık ve çözüm hemen gösterilir."""

    # Hata Avcısı modu: yalnızca daha önce yanlış yapılıp henüz doğru çözülmemiş sorular.
    mistakes_only = models.BooleanField(default=False)

    class Meta(BaseExamSession.Meta):
        verbose_name = "soru çözüm oturumu"
        verbose_name_plural = "soru çözüm oturumları"
        indexes = [models.Index(fields=("user", "started_at"))]

    def __str__(self):
        return f"{self.user} — soru çözümü #{self.pk}"


class TimedExamSession(BaseExamSession):
    """Süreli test. Bitiş zamanı sunucuda belirlenir; cevap anahtarı test bitmeden gönderilmez."""

    duration_seconds = models.PositiveIntegerField(validators=[MinValueValidator(60)])
    deadline = models.DateTimeField("bitiş zamanı")
    # Süre dolduğu için sunucunun bitirdiği test (öğrenci "Testi bitir"e basmadı).
    auto_finished = models.BooleanField(default=False)

    class Meta(BaseExamSession.Meta):
        verbose_name = "süreli test"
        verbose_name_plural = "süreli testler"
        indexes = [models.Index(fields=("user", "started_at"))]

    def __str__(self):
        return f"{self.user} — süreli test #{self.pk}"

    def remaining_seconds(self, now=None):
        now = now or timezone.now()
        return max(0, int((self.deadline - now).total_seconds()))


class ExamAnswer(models.Model):
    """Bir oturumdaki soruya verilen cevap. Her soru oturum başına tek kayıttır.

    Süreli testte öğrenci süre bitene kadar cevabını değiştirebilir (kayıt güncellenir);
    soru çözümünde cevap ilk gönderimde kesinleşir. `selected_option` boşsa soru boş bırakılmıştır.
    """

    practice_session = models.ForeignKey(
        PracticeSession, on_delete=models.CASCADE, null=True, blank=True, related_name="answers"
    )
    timed_session = models.ForeignKey(
        TimedExamSession, on_delete=models.CASCADE, null=True, blank=True, related_name="answers"
    )
    question_id = models.CharField("soru", max_length=64)
    selected_option = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "oturum cevabı"
        verbose_name_plural = "oturum cevapları"
        ordering = ("created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(practice_session__isnull=False, timed_session__isnull=True)
                    | models.Q(practice_session__isnull=True, timed_session__isnull=False)
                ),
                name="exam_answer_exactly_one_session",
            ),
            models.UniqueConstraint(
                fields=("practice_session", "question_id"),
                condition=models.Q(practice_session__isnull=False),
                name="unique_practice_answer",
            ),
            models.UniqueConstraint(
                fields=("timed_session", "question_id"),
                condition=models.Q(timed_session__isnull=False),
                name="unique_timed_answer",
            ),
        ]

    def __str__(self):
        return f"{self.question_id}: {self.selected_option or 'boş'}"

    @property
    def session(self):
        return self.practice_session or self.timed_session
