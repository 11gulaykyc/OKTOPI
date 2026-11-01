"""Kayıt sonrası başlangıç seviye testi (Onboarding Diagnostic).

Sorular soru havuzundan, öğrencinin sınıfı ve altındaki sınıflardan (temel bilgiler) seçilir;
kendi sınıfının soruları önceliklidir. Seçim deterministiktir: sunucu, öğrencinin cevapladığı
soru kümesini durum saklamadan yeniden hesaplayıp doğrulayabilir.
Puanlama zorluk ağırlıklıdır ve yalnızca sunucuda yapılır. Test bir ölçümdür: cevaplar istatistiklere
ve kavram yanılgısı kayıtlarına yazılır ama puan, rozet, görev veya hedef ilerlemesi kazandırmaz.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.analytics.models import MisconceptionLog
from apps.analytics.services import record_attempt
from apps.curriculum.content_loader import get_repository

from .models import StudentProfile

DIAGNOSTIC_SIZE = 8
DIFFICULTY_WEIGHT = {"easy": 1, "medium": 2, "hard": 3}
# Her konudan sırayla orta → kolay → zor soru alınır; böylece kısa testte zorluk dengeli olur.
DIFFICULTY_ORDER = ("medium", "easy", "hard")
# Ağırlıklı başarı oranına göre seviye eşikleri
LEVEL_THRESHOLDS = (
    (0.75, StudentProfile.InitialLevel.ADVANCED),
    (0.4, StudentProfile.InitialLevel.INTERMEDIATE),
    (0.0, StudentProfile.InitialLevel.BEGINNER),
)


class DiagnosticAlreadyDone(Exception):
    pass


def _topic_queue(questions):
    by_difficulty = {d: sorted((q for q in questions if q.difficulty == d), key=lambda q: q.id) for d in DIFFICULTY_ORDER}
    queue = []
    while any(by_difficulty.values()):
        for d in DIFFICULTY_ORDER:
            if by_difficulty[d]:
                queue.append(by_difficulty[d].pop(0))
    return queue


def diagnostic_questions(grade, size=DIAGNOSTIC_SIZE):
    """Öğrencinin sınıfı için tanılama soruları (deterministik, en fazla `size` soru)."""
    repo = get_repository()
    eligible = [q for q in repo.questions.values() if q.grade <= grade]
    # Önce kendi sınıfı, sonra bir alt sınıf ...; her sınıfta konular sırayla dolaşılır.
    selected = []
    for g in sorted({q.grade for q in eligible}, reverse=True):
        topics = sorted({q.topic_id for q in eligible if q.grade == g})
        queues = [_topic_queue([q for q in eligible if q.topic_id == t]) for t in topics]
        while any(queues) and len(selected) < size:
            for queue in queues:
                if queue and len(selected) < size:
                    selected.append(queue.pop(0))
        if len(selected) >= size:
            break
    return selected


def level_for(ratio):
    return next(level for threshold, level in LEVEL_THRESHOLDS if ratio >= threshold)


def submit_diagnostic(user, answers):
    """Cevapları değerlendirir, sonucu profile işler.

    `answers`: {soru_id: şık_harfi veya ""}. Cevaplanmayan sorular boş sayılır.
    """
    profile = user.profile
    questions = diagnostic_questions(profile.grade_level)
    if not questions:
        raise ValidationError("Şu an sınıfın için başlangıç sorusu bulunmuyor. Bu adımı atlayabilirsin.")
    allowed = {q.id for q in questions}
    unknown = set(answers) - allowed
    if unknown:
        raise ValidationError({"answers": "Testte olmayan soru gönderildi."})

    with transaction.atomic():
        profile = StudentProfile.objects.select_for_update().get(pk=profile.pk)
        if profile.initial_level_assessed_at is not None:
            raise DiagnosticAlreadyDone()
        earned = total = 0
        correct = 0
        topics = {}
        for question in questions:
            key = answers.get(question.id) or ""
            option = next((o for o in question.options if o.key == key), None)
            if key and option is None:
                raise ValidationError({"answers": f"{question.id}: böyle bir şık yok."})
            attempt, _ = record_attempt(user, question, option, source=MisconceptionLog.Source.DIAGNOSTIC)
            weight = DIFFICULTY_WEIGHT[question.difficulty]
            total += weight
            is_correct = bool(option and option.is_correct)
            if is_correct:
                earned += weight
                correct += 1
            topic = topics.setdefault(question.topic_id, {"topic_id": question.topic_id, "title": question.topic, "correct": 0, "total": 0})
            topic["total"] += 1
            topic["correct"] += int(is_correct)
        ratio = earned / total
        profile.initial_level_status = level_for(ratio)
        profile.initial_level_assessed_at = timezone.now()
        profile.save(update_fields=["initial_level_status", "initial_level_assessed_at", "updated_at"])
    return {
        "level": profile.initial_level_status,
        "level_display": profile.get_initial_level_status_display(),
        "correct": correct,
        "total": len(questions),
        "score": round(ratio, 3),
        "topics": list(topics.values()),
    }
