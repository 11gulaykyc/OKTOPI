from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class PointLedger(models.Model):
    """Puan hareketleri defteri. Toplam puan her zaman bu kayıtların toplamıdır.

    Aynı eylem için (ör. aynı testin bitirilmesi) mükerrer puan yazılmasını
    (user, idempotency_key) benzersiz kısıtı engeller.
    """

    class Reason(models.TextChoices):
        CORRECT_ANSWER = "correct_answer", "Doğru cevap"
        EXAM_COMPLETED = "exam_completed", "Test tamamlandı"
        TOPIC_COMPLETED = "topic_completed", "Konu tamamlandı"
        TASK_COMPLETED = "task_completed", "Görev tamamlandı"
        GOAL_REACHED = "goal_reached", "Hedefe ulaşıldı"
        BADGE_EARNED = "badge_earned", "Rozet kazanıldı"
        ADJUSTMENT = "adjustment", "Düzeltme"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="point_entries")
    amount = models.IntegerField()
    reason = models.CharField(max_length=24, choices=Reason.choices)
    description = models.CharField(max_length=200, blank=True)
    idempotency_key = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "puan hareketi"
        verbose_name_plural = "puan hareketleri"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=("user", "idempotency_key"), name="unique_point_idempotency_key"),
        ]
        indexes = [models.Index(fields=("user", "created_at"))]

    def __str__(self):
        return f"{self.user} {self.amount:+d} ({self.get_reason_display()})"


class Badge(models.Model):
    code = models.SlugField(max_length=48, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=255)
    icon = models.CharField("ikon adı (Lucide)", max_length=48, blank=True)
    points_reward = models.PositiveIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "rozet"
        verbose_name_plural = "rozetler"
        ordering = ("order", "id")

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.PROTECT, related_name="awards")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "kazanılan rozet"
        verbose_name_plural = "kazanılan rozetler"
        constraints = [models.UniqueConstraint(fields=("user", "badge"), name="unique_user_badge")]
        ordering = ("-awarded_at",)

    def __str__(self):
        return f"{self.user} — {self.badge}"


class DailyTask(models.Model):
    """Öğrenciye atanmış günlük/haftalık görev ve ilerlemesi."""

    class Period(models.TextChoices):
        DAILY = "daily", "Günlük"
        WEEKLY = "weekly", "Haftalık"

    class TaskType(models.TextChoices):
        SOLVE_QUESTIONS = "solve_questions", "Soru çöz"
        CORRECT_ANSWERS = "correct_answers", "Doğru cevap ver"
        STUDY_MINUTES = "study_minutes", "Aktif çalış (dakika)"
        COMPLETE_TOPIC = "complete_topic", "Konu tamamla"
        FINISH_EXAM = "finish_exam", "Süreli test bitir"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    period = models.CharField(max_length=8, choices=Period.choices)
    period_start = models.DateField("dönem başlangıcı")
    task_type = models.CharField(max_length=24, choices=TaskType.choices)
    title = models.CharField(max_length=120)
    target = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    progress = models.PositiveIntegerField(default=0)
    points_reward = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "görev"
        verbose_name_plural = "görevler"
        ordering = ("period_start", "period", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "period", "period_start", "task_type"), name="unique_task_per_period"
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.title} ({self.progress}/{self.target})"

    @property
    def is_completed(self):
        return self.completed_at is not None


class PersonalGoal(models.Model):
    """Öğrencinin kendi koyduğu hedef. Hedef değiştiğinde eski kayıt kapatılır (valid_until),
    yenisi açılır; böylece geçmiş günler eski hedefe göre değerlendirilmeye devam eder."""

    class GoalType(models.TextChoices):
        DAILY_QUESTIONS = "daily_questions", "Günlük soru sayısı"
        DAILY_MINUTES = "daily_minutes", "Günlük çalışma süresi (dk)"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    goal_type = models.CharField(max_length=24, choices=GoalType.choices)
    target = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "kişisel hedef"
        verbose_name_plural = "kişisel hedefler"
        ordering = ("-valid_from",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "goal_type"),
                condition=models.Q(valid_until__isnull=True),
                name="one_active_goal_per_type",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.get_goal_type_display()}: {self.target}"
