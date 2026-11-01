import calendar

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower

from .validators import UsernameValidator


class User(AbstractUser):
    """Platform kullanıcısı. E-posta benzersizdir ve girişte kullanıcı adı yerine kullanılabilir.
    Kullanıcı adı ve e-posta büyük/küçük harf fark etmeksizin veritabanı düzeyinde benzersizdir."""

    username = models.CharField(
        "kullanıcı adı",
        max_length=150,
        unique=True,
        validators=[UsernameValidator()],
        error_messages={"unique": "Bu kullanıcı adı alınmış."},
    )
    email = models.EmailField("e-posta", unique=True)

    class Meta:
        verbose_name = "kullanıcı"
        verbose_name_plural = "kullanıcılar"
        constraints = [
            models.UniqueConstraint(Lower("username"), name="user_username_ci_unique"),
            models.UniqueConstraint(Lower("email"), name="user_email_ci_unique"),
        ]


class StudentProfile(models.Model):
    # Doğum tarihinde yaş sınırı yoktur; yalnızca gelecek tarih ve 1900 öncesi (yazım hatası) reddedilir.
    MIN_BIRTH_YEAR = 1900

    class SchoolType(models.TextChoices):
        ANADOLU = "anadolu", "Anadolu Lisesi"
        FEN = "fen", "Fen Lisesi"

    class InitialLevel(models.TextChoices):
        NOT_ASSESSED = "not_assessed", "Henüz belirlenmedi"
        BEGINNER = "beginner", "Başlangıç"
        INTERMEDIATE = "intermediate", "Orta"
        ADVANCED = "advanced", "İleri"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    birth_date = models.DateField("doğum tarihi")
    school_type = models.CharField("okul türü", max_length=16, choices=SchoolType.choices)
    grade_level = models.PositiveSmallIntegerField(
        "sınıf düzeyi", validators=[MinValueValidator(9), MaxValueValidator(12)]
    )
    initial_level_status = models.CharField(
        "başlangıç seviye durumu",
        max_length=16,
        choices=InitialLevel.choices,
        default=InitialLevel.NOT_ASSESSED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "öğrenci profili"
        verbose_name_plural = "öğrenci profilleri"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(grade_level__gte=9, grade_level__lte=12),
                name="profile_grade_level_9_12",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.grade_level}. sınıf)"

    def age_on(self, day):
        b = self.birth_date
        return day.year - b.year - ((day.month, day.day) < (b.month, b.day))

    def is_birthday_on(self, day):
        b = self.birth_date
        if (b.month, b.day) == (day.month, day.day):
            return True
        # 29 Şubat doğumlular artık yıl olmayan yıllarda 28 Şubat'ta kutlanır.
        return (b.month, b.day) == (2, 29) and not calendar.isleap(day.year) and (day.month, day.day) == (2, 28)
