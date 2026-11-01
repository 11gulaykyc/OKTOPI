from collections import Counter
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.curriculum.content_loader import get_repository
from apps.gamification import engine
from apps.gamification.models import PersonalGoal, PointLedger
from apps.gamification.services import TOPIC_COMPLETION_POINTS, award_points, level_info, total_points
from apps.questions.serializers import recommendation
from apps.study_sessions.models import DailyStudyTotal

from .models import MisconceptionLog, QuestionAttempt, TopicProgress

# --- Gelişim Haritası / Hata Analizi eşikleri ---
# Bir konuda kesin değerlendirme yapmak için gereken en az (ilk deneme) cevap sayısı.
# Altında kalan konular "veri yetersiz" olarak sunulur; tanı gibi gösterilmez.
MIN_ANSWERS_FOR_DIAGNOSIS = 5
# Bir kavram yanılgısının "tekrarlayan örüntü" sayılması için en az kaç kez görülmesi gerekir.
MIN_REPEATS_FOR_PATTERN = 2
MASTERED_RATE = 0.8
DEVELOPING_RATE = 0.5


def log_misconception(user, question, option, source=MisconceptionLog.Source.PRACTICE):
    """Yanlış seçilen şıkkın kavram yanılgısını kaydeder.

    `question` ve `option`, content.schemas.QuestionSchema / QuestionOption nesneleridir.
    Doğru şık veya etiketsiz şık için kayıt oluşturulmaz.
    """
    if option.is_correct or not option.misconception_tag:
        return None
    return MisconceptionLog.objects.create(
        user=user,
        question_id=question.id,
        topic_id=question.topic_id,
        misconception_tag=option.misconception_tag,
        subtopic_id=option.recommended_subtopic_id,
        selected_option=option.key,
        source=source,
    )


def _progress_for(user, topic_id, grade):
    progress, _ = TopicProgress.objects.get_or_create(user=user, topic_id=topic_id, defaults={"grade": grade})
    return progress


def record_attempt(user, question, option, source=MisconceptionLog.Source.PRACTICE):
    """Bir cevabı kaydeder; konu ilerlemesini ve kavram yanılgısı kaydını günceller.

    `option` None ise soru boş bırakılmıştır. Konu başarı oranı sorunun yalnızca İLK
    cevabıyla hesaplanır; cevabı gördükten sonra tekrar denemek oranı şişirmez.
    """
    is_correct = bool(option and option.is_correct)
    with transaction.atomic():
        first_try = not QuestionAttempt.objects.filter(user=user, question_id=question.id).exists()
        attempt = QuestionAttempt.objects.create(
            user=user,
            question_id=question.id,
            grade=question.grade,
            topic_id=question.topic_id,
            selected_option=option.key if option else "",
            is_correct=is_correct,
            source=source,
        )
        progress = _progress_for(user, question.topic_id, question.grade)
        updates = {}
        if first_try:
            updates["questions_answered"] = F("questions_answered") + 1
            updates["correct_answers"] = F("correct_answers") + int(is_correct)
        if progress.status == TopicProgress.Status.NOT_STARTED:
            updates["status"] = TopicProgress.Status.IN_PROGRESS
        if updates:
            TopicProgress.objects.filter(pk=progress.pk).update(updated_at=timezone.now(), **updates)
        if option:
            log_misconception(user, question, option, source=source)
    return attempt, first_try


def save_last_section(user, topic_id, grade, section_id):
    """Konu anlatımında son görüntülenen bölümü ("son kalınan yer") kaydeder."""
    progress = _progress_for(user, topic_id, grade)
    progress.last_section_id = section_id
    if progress.status == TopicProgress.Status.NOT_STARTED:
        progress.status = TopicProgress.Status.IN_PROGRESS
    progress.save(update_fields=["last_section_id", "status", "updated_at"])
    return progress


def complete_topic(user, topic_id, grade):
    """Konuyu tamamlandı olarak işaretler. Ödül puanı konu başına bir kez yazılır.

    Döner: (ilerleme, bu istekte kazanılan puan)
    """
    with transaction.atomic():
        progress = TopicProgress.objects.select_for_update().filter(user=user, topic_id=topic_id).first()
        progress = progress or _progress_for(user, topic_id, grade)
        if progress.status != TopicProgress.Status.COMPLETED:
            progress.status = TopicProgress.Status.COMPLETED
            progress.completed_at = timezone.now()
            progress.save(update_fields=["status", "completed_at", "updated_at"])
        _, created = award_points(
            user,
            TOPIC_COMPLETION_POINTS,
            PointLedger.Reason.TOPIC_COMPLETED,
            idempotency_key=f"topic_completed:{topic_id}",
            description=f"{topic_id} tamamlandı",
        )
    return progress, TOPIC_COMPLETION_POINTS if created else 0


def serialize_progress(progress):
    ref = get_repository().topic_ref(progress.topic_id)
    return {
        "topic_id": progress.topic_id,
        "grade": progress.grade,
        "title": ref[2].title if ref else progress.topic_id,
        "status": progress.status,
        "last_section_id": progress.last_section_id,
        "questions_answered": progress.questions_answered,
        "correct_answers": progress.correct_answers,
        "success_rate": progress.success_rate,
        "completed_at": progress.completed_at,
        "updated_at": progress.updated_at,
    }


def _week_start(day):
    return day - timedelta(days=day.weekday())


def dashboard_summary(user, days=7):
    """Öğrenci paneli için özet istatistikler; yalnızca veritabanındaki gerçek kayıtlardan hesaplanır."""
    today = timezone.localdate()
    since = today - timedelta(days=days - 1)
    week_start = _week_start(today)

    # Çalışma süresi
    totals = DailyStudyTotal.objects.filter(user=user)
    seconds_by_day = dict(totals.filter(date__gte=since).values_list("date", "active_seconds"))
    study = {
        "total_seconds": totals.aggregate(s=Sum("active_seconds"))["s"] or 0,
        "today_seconds": seconds_by_day.get(today, 0),
        "week_seconds": totals.filter(date__gte=week_start).aggregate(s=Sum("active_seconds"))["s"] or 0,
        "active_days": totals.filter(active_seconds__gt=0).count(),
    }

    # Sorular
    attempts = QuestionAttempt.objects.filter(user=user)
    counts = attempts.aggregate(
        total=Count("id"),
        correct=Count("id", filter=Q(is_correct=True)),
        blank=Count("id", filter=Q(selected_option="")),
    )
    questions = {
        "total": counts["total"],
        "correct": counts["correct"],
        "incorrect": counts["total"] - counts["correct"] - counts["blank"],
        "blank": counts["blank"],
        "today": attempts.filter(created_at__date=today).count(),
        "week": attempts.filter(created_at__date__gte=week_start).count(),
    }
    answers_by_day = {
        row["day"]: row
        for row in attempts.filter(created_at__date__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"), correct=Count("id", filter=Q(is_correct=True)))
    }
    daily = []
    for offset in range(days):
        day = since + timedelta(days=offset)
        row = answers_by_day.get(day, {})
        daily.append(
            {
                "date": day,
                "study_seconds": seconds_by_day.get(day, 0),
                "questions": row.get("total", 0),
                "correct": row.get("correct", 0),
            }
        )

    # Konular
    progress = list(TopicProgress.objects.filter(user=user).order_by("-updated_at"))
    topics = {
        "started": sum(1 for p in progress if p.status != TopicProgress.Status.NOT_STARTED),
        "completed": sum(1 for p in progress if p.status == TopicProgress.Status.COMPLETED),
        # Başarı oranı yalnızca soru çözülmüş konular için anlamlıdır.
        "success": [serialize_progress(p) for p in progress if p.questions_answered],
    }

    # Görevler ve hedefler: oyunlaştırma motoru görevleri atar ve ilerlemeyi gerçek kayıtlardan hesaplar.
    tasks = [engine.serialize_task(t) for t in engine.refresh_tasks(user)]
    goals = [
        {
            "goal_type": goal.goal_type,
            "label": goal.get_goal_type_display(),
            "target": goal.target,
            "current": engine.goal_progress(user, goal.goal_type, today),
        }
        for goal in PersonalGoal.objects.filter(user=user, valid_until__isnull=True)
    ]

    return {
        "generated_at": timezone.now(),
        "study": study,
        "questions": questions,
        "daily": daily,
        "topics": topics,
        "recent_topics": [serialize_progress(p) for p in progress[:5]],
        "points": level_info(total_points(user)),
        "tasks": tasks,
        "goals": goals,
        "misconception_count": MisconceptionLog.objects.filter(user=user).count(),
    }


# --- Gelişim Haritası ve Hata Analizi ---


def default_grade(user):
    """Sınıf belirtilmezse öğrencinin profilindeki sınıf (profil yoksa 9) kullanılır."""
    try:
        return user.profile.grade_level
    except ObjectDoesNotExist:
        return 9


def open_mistakes(user, grade=None):
    """Son cevabı yanlış olan sorular: {soru_id: son QuestionAttempt}.

    Daha sonra doğru çözülen soru listeden düşer; boş bırakılan cevaplar yanlış sayılmaz.
    """
    qs = QuestionAttempt.objects.filter(user=user).exclude(selected_option="")
    if grade is not None:
        qs = qs.filter(grade=grade)
    latest = {}
    for attempt in qs.order_by("created_at", "id"):
        latest[attempt.question_id] = attempt
    return {qid: attempt for qid, attempt in latest.items() if not attempt.is_correct}


def mastery_level(answered, rate):
    """Konu düzeyi. Yeterli veri yoksa başarı oranı ne olursa olsun "insufficient" döner."""
    if not answered:
        return "not_started"
    if answered < MIN_ANSWERS_FOR_DIAGNOSIS:
        return "insufficient"
    if rate >= MASTERED_RATE:
        return "mastered"
    if rate >= DEVELOPING_RATE:
        return "developing"
    return "needs_review"


def _thresholds():
    return {
        "min_answers_for_diagnosis": MIN_ANSWERS_FOR_DIAGNOSIS,
        "min_repeats_for_pattern": MIN_REPEATS_FOR_PATTERN,
        "mastered_rate": MASTERED_RATE,
        "developing_rate": DEVELOPING_RATE,
    }


def _grade_topic_ids(grade):
    return {tid for tid, (g, _, _) in get_repository().topic_refs.items() if g == grade}


def mastery_map(user, grade):
    """Gelişim Haritası: sınıfın tüm konuları için ilerleme, düzey ve tekrar çalışılması gereken alanlar.

    Başarı oranı TopicProgress'teki ilk deneme cevaplarından hesaplanır (tekrar denemek oranı şişirmez).
    """
    repo = get_repository()
    curriculum = repo.curricula[grade]
    progress = {p.topic_id: p for p in TopicProgress.objects.filter(user=user, grade=grade)}
    open_by_topic = Counter(a.topic_id for a in open_mistakes(user, grade).values())
    misconceptions_by_topic = dict(
        MisconceptionLog.objects.filter(user=user, topic_id__in=_grade_topic_ids(grade))
        .values("topic_id")
        .annotate(n=Count("id"))
        .values_list("topic_id", "n")
    )
    question_counts = repo.question_counts_by_topic()

    themes, levels, review = [], Counter(), []
    for theme in sorted(curriculum.themes, key=lambda t: t.order):
        topics = []
        for ref in theme.topics:
            p = progress.get(ref.id)
            answered = p.questions_answered if p else 0
            rate = p.success_rate if p else None
            level = mastery_level(answered, rate)
            item = {
                "id": ref.id,
                "title": ref.title,
                "has_content": ref.id in repo.topics,
                "question_count": question_counts.get(ref.id, 0),
                "status": p.status if p else TopicProgress.Status.NOT_STARTED,
                "questions_answered": answered,
                "correct_answers": p.correct_answers if p else 0,
                "success_rate": rate,
                "level": level,
                "enough_data": answered >= MIN_ANSWERS_FOR_DIAGNOSIS,
                "answers_needed": max(0, MIN_ANSWERS_FOR_DIAGNOSIS - answered),
                "open_mistakes": open_by_topic.get(ref.id, 0),
                "misconception_count": misconceptions_by_topic.get(ref.id, 0),
            }
            # Tekrar listesi: kesin olarak zayıf görünen konular ve hâlâ düzeltilmemiş yanlışı olanlar.
            item["needs_review"] = level == "needs_review" or item["open_mistakes"] > 0
            levels[level] += 1
            if item["needs_review"]:
                review.append(item)
            topics.append(item)
        themes.append({"id": theme.id, "title": theme.title, "topics": topics})

    review.sort(key=lambda t: (t["level"] != "needs_review", -t["open_mistakes"], t["success_rate"] or 0))
    return {
        "grade": grade,
        "thresholds": _thresholds(),
        "levels": {key: levels.get(key, 0) for key in ("mastered", "developing", "needs_review", "insufficient", "not_started")},
        "themes": themes,
        "review": [
            {"id": t["id"], "title": t["title"], "level": t["level"], "open_mistakes": t["open_mistakes"]} for t in review
        ],
    }


def _misconception_details():
    """Etiket → açıklama tablosu; açıklamalar soru JSON'larındaki yanlış şıklardan gelir."""
    details = {}
    for question in get_repository().questions.values():
        for option in question.options:
            if option.misconception_tag and option.misconception_tag not in details:
                details[option.misconception_tag] = option.misconception_detail
    return details


def error_analysis(user, grade):
    """Kavram yanılgısı örüntüleri ve hâlâ düzeltilmemiş yanlış sorular.

    Doğru cevap anahtarı DÖNMEZ: öğrenci bu soruları Hata Avcısı modunda yeniden çözebilir.
    """
    repo = get_repository()
    mistakes = open_mistakes(user, grade)
    details = _misconception_details()

    patterns = {}
    logs = (
        MisconceptionLog.objects.filter(user=user, topic_id__in=_grade_topic_ids(grade))
        .order_by("-created_at", "-id")
        .values("misconception_tag", "question_id", "topic_id", "subtopic_id", "created_at")
    )
    for log in logs:
        tag = log["misconception_tag"]
        pattern = patterns.get(tag)
        if pattern is None:
            # Kayıtlar yeniden eskiye sıralı: bir etiketin ilk kaydı en güncel olanıdır.
            entry = repo.topic_ref(log["topic_id"])
            pattern = patterns[tag] = {
                "tag": tag,
                "detail": details.get(tag, ""),
                "topic_id": log["topic_id"],
                "topic_title": entry[2].title if entry else log["topic_id"],
                "recommended": recommendation(log["subtopic_id"]),
                "count": 0,
                "question_ids": set(),
                "last_seen": log["created_at"],
            }
        pattern["count"] += 1
        pattern["question_ids"].add(log["question_id"])

    result_patterns = []
    for pattern in patterns.values():
        question_ids = pattern.pop("question_ids")
        open_questions = sum(1 for qid in question_ids if qid in mistakes)
        result_patterns.append(
            {
                **pattern,
                "question_count": len(question_ids),
                "recurring": pattern["count"] >= MIN_REPEATS_FOR_PATTERN,
                "open_questions": open_questions,
                # Bu yanılgının görüldüğü tüm sorular sonradan doğru çözüldüyse yanılgı aşılmış sayılır.
                "resolved": open_questions == 0,
            }
        )
    result_patterns.sort(key=lambda p: (p["resolved"], -p["count"], -p["last_seen"].timestamp()))

    mistake_items = []
    for qid, attempt in sorted(mistakes.items(), key=lambda kv: kv[1].created_at, reverse=True):
        question = repo.questions.get(qid)
        if question is None:  # içerikten kaldırılmış soru
            continue
        option = next((o for o in question.options if o.key == attempt.selected_option), None)
        mistake_items.append(
            {
                "question_id": qid,
                "topic_id": question.topic_id,
                "topic": question.topic,
                "subtopic": question.subtopic,
                "difficulty": question.difficulty,
                "question_text": question.question_text,
                "selected_option": attempt.selected_option,
                "selected_text": option.text if option else "",
                "misconception": (
                    {"tag": option.misconception_tag, "detail": option.misconception_detail}
                    if option and option.misconception_tag
                    else None
                ),
                "recommended": (
                    recommendation(option.recommended_subtopic_id) if option and option.recommended_subtopic_id else None
                ),
                "answered_at": attempt.created_at,
            }
        )

    answered = TopicProgress.objects.filter(user=user, grade=grade).aggregate(n=Sum("questions_answered"))["n"] or 0
    return {
        "grade": grade,
        "thresholds": _thresholds(),
        "enough_data": answered >= MIN_ANSWERS_FOR_DIAGNOSIS,
        "totals": {
            "answered": answered,
            "misconception_logs": sum(p["count"] for p in result_patterns),
            "patterns": len(result_patterns),
            "recurring_patterns": sum(1 for p in result_patterns if p["recurring"] and not p["resolved"]),
            "open_mistakes": len(mistake_items),
        },
        "patterns": result_patterns,
        "mistakes": mistake_items,
    }
