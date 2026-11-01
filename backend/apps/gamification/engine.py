"""Oyunlaştırma motoru: gerçek eylemlere bağlı puan, rozet, görev ve hedef ödülleri.

Diğer uygulamalar yalnızca `on_*` olay fonksiyonlarını çağırır. Her ödül `transaction.atomic()`
içinde ve tekil anahtarla (PointLedger.idempotency_key / UserBadge benzersiz kısıtı) yazılır;
aynı olay tekrar işlense de (çift tıklama, tekrarlanan istek) ikinci kez ödül verilmez.

Görev ve hedef ilerlemesi sayaç artırılarak değil, her seferinde veritabanındaki gerçek
kayıtlardan yeniden hesaplanır. Böylece tekrarlanan olaylar ilerlemeyi şişiremez.
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.analytics.models import MisconceptionLog, QuestionAttempt, TopicProgress
from apps.exams.models import TimedExamSession
from apps.study_sessions.models import DailyStudyTotal

from .models import Badge, DailyTask, PersonalGoal, PointLedger, UserBadge
from .services import award_points

# --- Puanlar ---
# Doğru cevap puanı her soru için ömür boyu bir kez verilir (idempotency_key: answer:<soru>).
CORRECT_ANSWER_POINTS = 10
# Süreli test bitirme bonusu: soruların en az yarısı cevaplanmış olmalı; günde en fazla 3 kez.
EXAM_COMPLETION_POINTS = 20
EXAM_MIN_ANSWERED_RATIO = 0.5
MAX_EXAM_BONUSES_PER_DAY = 3
GOAL_REACHED_POINTS = 15

# --- Rozet eşikleri ---
CURIOUS_MIN_TOPICS = 3  # Meraklı Zihin: 3 farklı konuya başla
EXPLORER_MIN_TOPICS = 3  # Matematik Kaşifi: 3 farklı konuda doğru cevap ver
STREAK_DAYS = 3  # İstikrarlı Öğrenci: art arda 3 gün çalış
STREAK_MIN_SECONDS = 5 * 60  # bir günün "çalışılmış" sayılması için en az 5 dk aktif süre
SPEED_MIN_QUESTIONS = 5  # Hız Ustası: en az 5 soruluk süreli test,
SPEED_MIN_SUCCESS = 0.8  # en az %80 doğru,
SPEED_MAX_TIME_RATIO = 0.5  # sürenin en fazla yarısında, kendi isteğiyle bitirilmiş

# Rozet adları/açıklamaları/ödül puanları veritabanındadır (gamification/migrations/0002_seed_badges.py);
# burada yalnızca kazanım kuralları vardır. Kod (ör. "hiz-ustasi") iki yerde aynı olmalıdır.

# Her dönem başında öğrenciye atanan görevler: (dönem, tür, başlık, hedef, ödül puanı)
TASK_TEMPLATES = (
    (DailyTask.Period.DAILY, DailyTask.TaskType.SOLVE_QUESTIONS, "Bugün 10 farklı soru çöz", 10, 20),
    (DailyTask.Period.DAILY, DailyTask.TaskType.STUDY_MINUTES, "Bugün 20 dakika aktif çalış", 20, 20),
    (DailyTask.Period.WEEKLY, DailyTask.TaskType.CORRECT_ANSWERS, "Bu hafta 30 soruyu doğru çöz", 30, 50),
    (DailyTask.Period.WEEKLY, DailyTask.TaskType.FINISH_EXAM, "Bu hafta 2 süreli test bitir", 2, 40),
    (DailyTask.Period.WEEKLY, DailyTask.TaskType.COMPLETE_TOPIC, "Bu hafta 1 konuyu tamamla", 1, 30),
)


@dataclass
class Rewards:
    """Bir istekte kazanılan ödüller; istemci bunları maskot geri bildirimiyle gösterir."""

    points: int = 0
    badges: list = field(default_factory=list)
    tasks: list = field(default_factory=list)
    goals: list = field(default_factory=list)

    def add_points(self, entry, created):
        if created:
            self.points += entry.amount

    def merge(self, other):
        self.points += other.points
        self.badges += other.badges
        self.tasks += other.tasks
        self.goals += other.goals
        return self

    def as_dict(self):
        return {"points": self.points, "badges": self.badges, "tasks": self.tasks, "goals": self.goals}


# --- Yardımcılar ---


def week_start(day):
    return day - timedelta(days=day.weekday())


def _day_bounds(first_day, days=1):
    """Yerel (Europe/Istanbul) gün aralığını [başlangıç, bitiş) zaman damgalarına çevirir."""
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(first_day, time.min), tz)
    end = timezone.make_aware(datetime.combine(first_day + timedelta(days=days), time.min), tz)
    return start, end


def _rewardable_attempts(user):
    """Ödüle sayılan cevaplar. Başlangıç seviye testi bir ölçümdür; puan, rozet, görev ve hedeflere sayılmaz."""
    return QuestionAttempt.objects.filter(user=user).exclude(source=MisconceptionLog.Source.DIAGNOSTIC)


def _answered_questions(user, start, end, correct_only=False):
    """Aralıkta cevaplanan FARKLI soru sayısı (aynı soruyu tekrar çözmek sayıyı artırmaz; boşlar sayılmaz)."""
    qs = _rewardable_attempts(user).filter(created_at__gte=start, created_at__lt=end).exclude(selected_option="")
    if correct_only:
        qs = qs.filter(is_correct=True)
    return qs.values("question_id").distinct().count()


def _study_minutes(user, first_day, days=1):
    total = DailyStudyTotal.objects.filter(
        user=user, date__gte=first_day, date__lt=first_day + timedelta(days=days)
    ).aggregate(s=Sum("active_seconds"))["s"]
    return (total or 0) // 60


def _qualifying_exams(user):
    """Görev ve bonus için sayılan süreli testler: bitmiş ve soruların en az yarısı cevaplanmış."""
    exams = TimedExamSession.objects.filter(user=user, finished_at__isnull=False)
    return [e for e in exams if e.question_count and e.answered_count / e.question_count >= EXAM_MIN_ANSWERED_RATIO]


def award_badge(user, code, rewards):
    badge = Badge.objects.filter(code=code, is_active=True).first()
    if badge is None:
        return
    with transaction.atomic():
        _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        if not created:
            return
        if badge.points_reward:
            rewards.add_points(
                *award_points(
                    user,
                    badge.points_reward,
                    PointLedger.Reason.BADGE_EARNED,
                    idempotency_key=f"badge:{code}",
                    description=f"{badge.name} rozeti",
                )
            )
    rewards.badges.append(
        {"code": badge.code, "name": badge.name, "description": badge.description, "icon": badge.icon}
    )


def _earned_codes(user):
    return set(UserBadge.objects.filter(user=user).values_list("badge__code", flat=True))


# --- Rozet kuralları ---


def _check_topic_badges(user, earned, rewards):
    if "merakli-zihin" not in earned:
        # Konu anlatımını açmak, konuyu tamamlamak veya (başlangıç testi dışında) sorusunu çözmek "başlamak" sayılır.
        opened = TopicProgress.objects.filter(user=user).filter(
            ~Q(last_section_id="") | Q(status=TopicProgress.Status.COMPLETED)
        ).values_list("topic_id", flat=True)
        practiced = _rewardable_attempts(user).values_list("topic_id", flat=True)
        if len(set(opened) | set(practiced)) >= CURIOUS_MIN_TOPICS:
            award_badge(user, "merakli-zihin", rewards)
    if "matematik-kasifi" not in earned:
        topics = (
            _rewardable_attempts(user).filter(is_correct=True).values("topic_id").distinct().count()
        )
        if topics >= EXPLORER_MIN_TOPICS:
            award_badge(user, "matematik-kasifi", rewards)


def _check_streak(user, earned, rewards):
    if "istikrarli-ogrenci" in earned:
        return
    today = timezone.localdate()
    days = set(
        DailyStudyTotal.objects.filter(
            user=user, date__gt=today - timedelta(days=STREAK_DAYS), active_seconds__gte=STREAK_MIN_SECONDS
        ).values_list("date", flat=True)
    )
    if all(today - timedelta(days=i) in days for i in range(STREAK_DAYS)):
        award_badge(user, "istikrarli-ogrenci", rewards)


# --- Hedefler ---


def goal_progress(user, goal_type, day):
    """Kişisel hedefin bir gündeki gerçekleşen değeri (farklı soru sayısı veya aktif dakika)."""
    if goal_type == PersonalGoal.GoalType.DAILY_QUESTIONS:
        return _answered_questions(user, *_day_bounds(day))
    return _study_minutes(user, day)


def _check_goals(user, earned, rewards):
    today = timezone.localdate()
    for goal in PersonalGoal.objects.filter(user=user, valid_until__isnull=True):
        if goal_progress(user, goal.goal_type, today) < goal.target:
            continue
        entry, created = award_points(
            user,
            GOAL_REACHED_POINTS,
            PointLedger.Reason.GOAL_REACHED,
            idempotency_key=f"goal:{goal.goal_type}:{today.isoformat()}",
            description=f"{goal.get_goal_type_display()} hedefi ({goal.target})",
        )
        if created:
            rewards.add_points(entry, created)
            rewards.goals.append({"goal_type": goal.goal_type, "label": goal.get_goal_type_display(), "target": goal.target})
        if "hedef-tamamlandi" not in earned:
            award_badge(user, "hedef-tamamlandi", rewards)
            earned.add("hedef-tamamlandi")


def set_goal(user, goal_type, target, now=None):
    """Hedefi günceller. Eski kayıt silinmez, kapatılır (valid_until); geçmiş günler eski hedefe göre kalır."""
    now = now or timezone.now()
    with transaction.atomic():
        current = PersonalGoal.objects.select_for_update().filter(user=user, goal_type=goal_type, valid_until__isnull=True).first()
        if current and current.target == target:
            return current
        if current:
            current.valid_until = now
            current.save(update_fields=["valid_until"])
        return PersonalGoal.objects.create(user=user, goal_type=goal_type, target=target, valid_from=now)


def clear_goal(user, goal_type, now=None):
    now = now or timezone.now()
    return PersonalGoal.objects.filter(user=user, goal_type=goal_type, valid_until__isnull=True).update(valid_until=now)


def goal_history(user, days=14):
    """Son `days` günün hedef/gerçekleşme tablosu. Her gün, o günün sonunda geçerli olan hedefle değerlendirilir."""
    today = timezone.localdate()
    first = today - timedelta(days=days - 1)
    goals = list(PersonalGoal.objects.filter(user=user).order_by("valid_from"))
    rows = []
    for offset in range(days):
        day = first + timedelta(days=offset)
        start, end = _day_bounds(day)
        row = {"date": day}
        for goal_type in PersonalGoal.GoalType.values:
            # O gün içinde geçerli olmuş hedeflerden en son konulanı
            active = [
                g for g in goals
                if g.goal_type == goal_type and g.valid_from < end and (g.valid_until is None or g.valid_until > start)
            ]
            goal = active[-1] if active else None
            current = goal_progress(user, goal_type, day)
            row[goal_type] = {
                "target": goal.target if goal else None,
                "current": current,
                "reached": bool(goal and current >= goal.target),
            }
        rows.append(row)
    return rows


# --- Görevler ---


def _task_progress(user, task):
    days = 1 if task.period == DailyTask.Period.DAILY else 7
    start, end = _day_bounds(task.period_start, days)
    kind = task.task_type
    if kind == DailyTask.TaskType.SOLVE_QUESTIONS:
        return _answered_questions(user, start, end)
    if kind == DailyTask.TaskType.CORRECT_ANSWERS:
        return _answered_questions(user, start, end, correct_only=True)
    if kind == DailyTask.TaskType.STUDY_MINUTES:
        return _study_minutes(user, task.period_start, days)
    if kind == DailyTask.TaskType.COMPLETE_TOPIC:
        return TopicProgress.objects.filter(
            user=user, status=TopicProgress.Status.COMPLETED, completed_at__gte=start, completed_at__lt=end
        ).count()
    if kind == DailyTask.TaskType.FINISH_EXAM:
        return sum(1 for e in _qualifying_exams(user) if start <= e.finished_at < end)
    return 0


def ensure_tasks(user, today=None):
    """Bugünün ve bu haftanın görevlerini (yoksa) oluşturur."""
    today = today or timezone.localdate()
    starts = {DailyTask.Period.DAILY: today, DailyTask.Period.WEEKLY: week_start(today)}
    existing = set(
        DailyTask.objects.filter(
            user=user, period_start__in=set(starts.values())
        ).values_list("period", "period_start", "task_type")
    )
    missing = [
        DailyTask(
            user=user, period=period, period_start=starts[period], task_type=kind,
            title=title, target=target, points_reward=reward,
        )
        for period, kind, title, target, reward in TASK_TEMPLATES
        if (period, starts[period], kind) not in existing
    ]
    if missing:
        DailyTask.objects.bulk_create(missing, ignore_conflicts=True)
    # Haftanın ilk günü günlük ve haftalık başlangıç aynıdır; bu yüzden dönem + başlangıç birlikte eşlenir.
    current = Q()
    for period, start in starts.items():
        current |= Q(period=period, period_start=start)
    return DailyTask.objects.filter(current, user=user).order_by("period", "id")


def refresh_tasks(user, rewards=None, today=None):
    """Güncel görevlerin ilerlemesini gerçek kayıtlardan hesaplar; hedefe ulaşanları bir kez ödüllendirir."""
    rewards = rewards if rewards is not None else Rewards()
    tasks = list(ensure_tasks(user, today))
    for task in tasks:
        progress = _task_progress(user, task)
        if progress != task.progress:
            task.progress = progress
            DailyTask.objects.filter(pk=task.pk).update(progress=progress)
        if task.completed_at or progress < task.target:
            continue
        with transaction.atomic():
            locked = DailyTask.objects.select_for_update().get(pk=task.pk)
            if locked.completed_at:
                continue
            locked.completed_at = timezone.now()
            locked.save(update_fields=["completed_at"])
            task.completed_at = locked.completed_at
            if task.points_reward:
                rewards.add_points(
                    *award_points(
                        user,
                        task.points_reward,
                        PointLedger.Reason.TASK_COMPLETED,
                        idempotency_key=f"task:{task.pk}",
                        description=task.title,
                    )
                )
            rewards.tasks.append({"id": task.pk, "title": task.title, "points_reward": task.points_reward})
    return tasks


def serialize_task(task):
    return {
        "id": task.id,
        "period": task.period,
        "period_start": task.period_start,
        "task_type": task.task_type,
        "title": task.title,
        "target": task.target,
        "progress": min(task.progress, task.target),
        "points_reward": task.points_reward,
        "completed": task.completed_at is not None,
        "completed_at": task.completed_at,
    }


# --- Olaylar ---


def on_answer(user, attempt, deferred=False):
    """Bir soru cevabı kaydedildikten sonra çağrılır (`analytics.services.record_attempt` sonrası).

    `deferred=True`: toplu değerlendirmede (süreli test bitişi) konu rozetleri, hedef ve görev
    hesapları her soru için tekrarlanmaz; çağıran taraf sonunda bunları bir kez yapar.
    """
    rewards = Rewards()
    earned = _earned_codes(user)
    if attempt.is_correct:
        rewards.add_points(
            *award_points(
                user,
                CORRECT_ANSWER_POINTS,
                PointLedger.Reason.CORRECT_ANSWER,
                idempotency_key=f"answer:{attempt.question_id}",
                description=f"{attempt.question_id} doğru",
            )
        )
    if attempt.selected_option and "ilk-adim" not in earned:
        award_badge(user, "ilk-adim", rewards)
    if attempt.is_correct and "hata-avcisi" not in earned:
        had_mistake = (
            QuestionAttempt.objects.filter(user=user, question_id=attempt.question_id, is_correct=False, created_at__lt=attempt.created_at)
            .exclude(selected_option="")
            .exclude(pk=attempt.pk)
            .exists()
        )
        if had_mistake:
            award_badge(user, "hata-avcisi", rewards)
    if not deferred:
        _check_topic_badges(user, earned, rewards)
        _check_goals(user, earned, rewards)
        refresh_tasks(user, rewards)
    return rewards


def on_exam_finished(user, session):
    """Süreli test bittiğinde (elle veya süre dolunca) çağrılır."""
    rewards = Rewards()
    earned = _earned_codes(user)
    if session.question_count and session.answered_count / session.question_count >= EXAM_MIN_ANSWERED_RATIO:
        today_start, today_end = _day_bounds(timezone.localdate())
        bonuses_today = PointLedger.objects.filter(
            user=user, reason=PointLedger.Reason.EXAM_COMPLETED, created_at__gte=today_start, created_at__lt=today_end
        ).count()
        if bonuses_today < MAX_EXAM_BONUSES_PER_DAY:
            rewards.add_points(
                *award_points(
                    user,
                    EXAM_COMPLETION_POINTS,
                    PointLedger.Reason.EXAM_COMPLETED,
                    idempotency_key=f"exam:{session.pk}",
                    description="Süreli test tamamlandı",
                )
            )
    if "hiz-ustasi" not in earned and not session.auto_finished and session.question_count >= SPEED_MIN_QUESTIONS:
        used = (session.finished_at - session.started_at).total_seconds()
        if (
            session.correct_count / session.question_count >= SPEED_MIN_SUCCESS
            and used <= session.duration_seconds * SPEED_MAX_TIME_RATIO
        ):
            award_badge(user, "hiz-ustasi", rewards)
    _check_topic_badges(user, earned, rewards)
    _check_goals(user, earned, rewards)
    refresh_tasks(user, rewards)
    return rewards


def on_topic_activity(user):
    """Konuya başlama veya konu tamamlama sonrasında çağrılır."""
    rewards = Rewards()
    _check_topic_badges(user, _earned_codes(user), rewards)
    refresh_tasks(user, rewards)
    return rewards


def on_goal_changed(user):
    rewards = Rewards()
    _check_goals(user, _earned_codes(user), rewards)
    return rewards


def on_study_time(user):
    """Heartbeat süre kredilendirdiğinde çağrılır."""
    rewards = Rewards()
    earned = _earned_codes(user)
    _check_streak(user, earned, rewards)
    _check_goals(user, earned, rewards)
    refresh_tasks(user, rewards)
    return rewards
