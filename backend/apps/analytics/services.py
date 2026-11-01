from datetime import timedelta

from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.curriculum.content_loader import get_repository
from apps.gamification.models import DailyTask, PersonalGoal, PointLedger
from apps.gamification.services import TOPIC_COMPLETION_POINTS, award_points, level_info, total_points
from apps.study_sessions.models import DailyStudyTotal

from .models import MisconceptionLog, QuestionAttempt, TopicProgress


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

    # Görevler ve hedefler (görev ataması Faz 3 oyunlaştırma motorundadır; burada yalnızca mevcut kayıtlar okunur)
    tasks = [
        {
            "id": t.id,
            "period": t.period,
            "title": t.title,
            "target": t.target,
            "progress": min(t.progress, t.target),
            "points_reward": t.points_reward,
            "completed": t.is_completed,
        }
        for t in DailyTask.objects.filter(
            Q(period=DailyTask.Period.DAILY, period_start=today)
            | Q(period=DailyTask.Period.WEEKLY, period_start=week_start),
            user=user,
        )
    ]
    goals = []
    for goal in PersonalGoal.objects.filter(user=user, valid_until__isnull=True):
        if goal.goal_type == PersonalGoal.GoalType.DAILY_QUESTIONS:
            current = questions["today"]
        else:
            current = study["today_seconds"] // 60
        goals.append({"goal_type": goal.goal_type, "label": goal.get_goal_type_display(), "target": goal.target, "current": current})

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
