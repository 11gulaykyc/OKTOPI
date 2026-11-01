"""Soru çözümü ve süreli test motoru.

KURALLAR
- Cevap anahtarı yalnızca sunucudadır. Soru çözümünde doğru şık ve çözüm cevap gönderildikten sonra,
  süreli testte ise yalnızca test bittikten sonra döner.
- Süreli testin başlangıç ve bitiş zamanı sunucuda tutulur. Süre dolduktan sonra gelen cevap kabul
  edilmez; test, bir sonraki istekte (durum, cevap veya bitir) sunucu tarafından otomatik bitirilir.
- Cevaplar `ExamAnswer` tablosuna, panel istatistikleri ve kavram yanılgıları ise
  `analytics.record_attempt` üzerinden QuestionAttempt / MisconceptionLog tablolarına yazılır.
"""

import math
import random
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.analytics.models import MisconceptionLog, QuestionAttempt
from apps.analytics.services import record_attempt
from apps.curriculum.content_loader import get_repository
from apps.gamification import engine
from apps.questions.serializers import evaluation_result, public_question

from .models import ExamAnswer, PracticeSession, TimedExamSession

MAX_QUESTIONS = 30
DEFAULT_QUESTIONS = 10
# Varsayılan süre: soru başına 90 sn.
SECONDS_PER_QUESTION = 90
# Ağ gecikmesi payı: son saniyede gönderilen cevap, birkaç saniye geç ulaşsa da kabul edilir.
DEADLINE_GRACE = timedelta(seconds=5)


class ExamConflict(APIException):
    status_code = 409
    default_detail = "Bu işlem oturumun şu anki durumunda yapılamaz."
    default_code = "conflict"


class ExamTimeUp(ExamConflict):
    default_detail = "Süre doldu; test otomatik olarak tamamlandı."
    default_code = "time_up"


# --- Soru seçimi ---


def open_mistake_ids(user):
    """Son cevabı yanlış olan sorular (daha önce yanlış yapılmış ve sonradan doğru çözülmemiş)."""
    latest = {}
    for question_id, is_correct in (
        QuestionAttempt.objects.filter(user=user).exclude(selected_option="").order_by("created_at", "id")
        .values_list("question_id", "is_correct")
    ):
        latest[question_id] = is_correct
    return {qid for qid, ok in latest.items() if not ok}


def pick_questions(user, grade, topic_id="", subtopic_id="", difficulty="", count=DEFAULT_QUESTIONS, mistakes_only=False):
    pool = get_repository().questions_for(
        grade=grade, topic_id=topic_id or None, subtopic_id=subtopic_id or None, difficulty=difficulty or None
    )
    if mistakes_only:
        open_ids = open_mistake_ids(user)
        pool = [q for q in pool if q.id in open_ids]
        if not pool:
            raise ValidationError("Bu seçimde tekrar çözülecek yanlışın yok. Harika!")
    if not pool:
        raise ValidationError("Bu seçimle çözülecek soru bulunamadı. Başka bir konu veya zorluk dene.")
    return [q.id for q in random.sample(pool, min(count, len(pool)))]


def start_practice(user, grade, count=DEFAULT_QUESTIONS, mistakes_only=False, **filters):
    ids = pick_questions(user, grade, count=count, mistakes_only=mistakes_only, **filters)
    return PracticeSession.objects.create(
        user=user, grade=grade, topic_id=filters.get("topic_id", ""), question_ids=ids, mistakes_only=mistakes_only
    )


def start_timed_exam(user, grade, count=DEFAULT_QUESTIONS, duration_minutes=None, **filters):
    ids = pick_questions(user, grade, count=count, **filters)
    minutes = duration_minutes or max(1, math.ceil(len(ids) * SECONDS_PER_QUESTION / 60))
    now = timezone.now()
    return TimedExamSession.objects.create(
        user=user,
        grade=grade,
        topic_id=filters.get("topic_id", ""),
        question_ids=ids,
        started_at=now,
        duration_seconds=minutes * 60,
        deadline=now + timedelta(minutes=minutes),
    )


# --- Ortak yardımcılar ---


def _session_question(session, question_id):
    if question_id not in session.question_ids:
        raise ValidationError({"question_id": "Bu soru bu oturuma ait değil."})
    question = get_repository().questions.get(question_id)
    if question is None:
        raise ValidationError({"question_id": "Soru artık soru havuzunda bulunmuyor."})
    return question


def _option(question, key):
    if not key:
        return None
    option = next((o for o in question.options if o.key == key), None)
    if option is None:
        raise ValidationError({"selected_option": "Bu soruda böyle bir şık yok."})
    return option


def _questions(session):
    """Oturumdaki soruları sabit sırayla döner; içerikten kaldırılmış sorular atlanır."""
    repo = get_repository()
    return [q for q in (repo.questions.get(qid) for qid in session.question_ids) if q is not None]


# --- Soru çözümü ---


def submit_practice_answer(session, question_id, option_key):
    """Cevabı kesinleştirir ve hemen değerlendirir. Aynı soruya oturumda ikinci cevap kabul edilmez."""
    if session.is_finished:
        raise ExamConflict("Bu soru çözüm oturumu bitti.")
    question = _session_question(session, question_id)
    option = _option(question, option_key)
    if option is None:
        raise ValidationError({"selected_option": "Bir şık seçmelisin."})
    with transaction.atomic():
        try:
            with transaction.atomic():
                ExamAnswer.objects.create(
                    practice_session=session, question_id=question.id, selected_option=option.key, is_correct=option.is_correct
                )
        except IntegrityError:
            raise ExamConflict("Bu soruyu bu oturumda zaten cevapladın.") from None
        attempt, first_try = record_attempt(session.user, question, option, source=MisconceptionLog.Source.PRACTICE)
    rewards = engine.on_answer(session.user, attempt)
    if rewards.points or rewards.badges or rewards.tasks or rewards.goals:
        # Oturum boyunca kazanılanlar sonuç ekranında da gösterilsin.
        with transaction.atomic():
            locked = PracticeSession.objects.select_for_update().get(pk=session.pk)
            locked.rewards = engine.Rewards(**(locked.rewards or {})).merge(rewards).as_dict()
            locked.save(update_fields=["rewards"])
    return {**evaluation_result(question, option, first_try), "rewards": rewards.as_dict()}


def finish_practice(session):
    with transaction.atomic():
        session = PracticeSession.objects.select_for_update().get(pk=session.pk)
        if session.is_finished:
            return session
        answers = list(session.answers.all())
        session.correct_count = sum(1 for a in answers if a.is_correct)
        session.incorrect_count = len(answers) - session.correct_count
        session.blank_count = max(0, session.question_count - len(answers))
        session.finished_at = timezone.now()
        session.save(update_fields=["correct_count", "incorrect_count", "blank_count", "finished_at"])
    return session


# --- Süreli test ---


def is_expired(session, now=None):
    return (now or timezone.now()) > session.deadline + DEADLINE_GRACE


def expire_if_needed(session):
    """Süresi geçmiş ama bitirilmemiş testi sunucu tarafında tamamlar."""
    if not session.is_finished and is_expired(session):
        return finish_timed_exam(session, auto=True)
    return session


def submit_timed_answer(session, question_id, option_key):
    """Cevabı kaydeder (veya `option_key` boşsa temizler). Doğruluk bilgisi istemciye DÖNMEZ."""
    time_up = False
    with transaction.atomic():
        session = TimedExamSession.objects.select_for_update().get(pk=session.pk)
        if session.is_finished:
            if session.auto_finished:
                raise ExamTimeUp()
            raise ExamConflict("Test bitti; cevaplar artık değiştirilemez.")
        if is_expired(session):
            time_up = True
        else:
            question = _session_question(session, question_id)
            option = _option(question, option_key)
            ExamAnswer.objects.update_or_create(
                timed_session=session,
                question_id=question.id,
                defaults={"selected_option": option.key if option else "", "is_correct": bool(option and option.is_correct)},
            )
    if time_up:
        finish_timed_exam(session, auto=True)
        raise ExamTimeUp()
    return {
        "question_id": question_id,
        "selected_option": option_key or "",
        "answered_count": session.answers.exclude(selected_option="").count(),
        "remaining_seconds": session.remaining_seconds(),
    }


def finish_timed_exam(session, auto=False):
    """Testi bitirir: cevapları değerlendirir, istatistik/yanılgı kayıtlarını ve ödülleri yazar.

    Tekrar çağrılırsa (çift tıklama, eşzamanlı istek) hiçbir şey yeniden yazılmaz.
    """
    with transaction.atomic():
        session = TimedExamSession.objects.select_for_update().get(pk=session.pk)
        if session.is_finished:
            return session
        now = timezone.now()
        # Süre bittikten sonra gelen bitirme isteği (ör. istemcide sayaç sıfırlandı) da "süre doldu" sayılır.
        auto = auto or now >= session.deadline
        answers = {a.question_id: a for a in session.answers.all()}
        rewards = engine.Rewards()
        correct = incorrect = blank = 0
        for question in _questions(session):
            answer = answers.get(question.id)
            option = next((o for o in question.options if answer and o.key == answer.selected_option), None)
            attempt, _ = record_attempt(session.user, question, option, source=MisconceptionLog.Source.TIMED_EXAM)
            rewards.merge(engine.on_answer(session.user, attempt, deferred=True))
            if option is None:
                blank += 1
            elif option.is_correct:
                correct += 1
            else:
                incorrect += 1
        session.correct_count, session.incorrect_count, session.blank_count = correct, incorrect, blank
        session.finished_at = min(now, session.deadline) if auto else now
        session.auto_finished = auto
        session.save(update_fields=["correct_count", "incorrect_count", "blank_count", "finished_at", "auto_finished"])
        rewards.merge(engine.on_exam_finished(session.user, session))
        session.rewards = rewards.as_dict()
        session.save(update_fields=["rewards"])
    return session


# --- Çıktılar ---


def session_kind(session):
    return "timed" if isinstance(session, TimedExamSession) else "practice"


def _base(session):
    return {
        "id": session.pk,
        "type": session_kind(session),
        "grade": session.grade,
        "topic_id": session.topic_id,
        "topic_title": _topic_title(session.topic_id),
        "started_at": session.started_at,
        "finished_at": session.finished_at,
        "is_finished": session.is_finished,
        "question_count": session.question_count,
    }


def _topic_title(topic_id):
    entry = get_repository().topic_ref(topic_id) if topic_id else None
    return entry[2].title if entry else ""


def session_state(session):
    """Devam eden (veya biten) oturumun durumu. Süreli testte doğruluk bilgisi içermez."""
    questions = _questions(session)
    answers = {a.question_id: a for a in session.answers.all()}
    data = {**_base(session), "questions": [public_question(q) for q in questions], "server_now": timezone.now()}
    if isinstance(session, TimedExamSession):
        data.update(
            duration_seconds=session.duration_seconds,
            deadline=session.deadline,
            remaining_seconds=session.remaining_seconds() if not session.is_finished else 0,
            auto_finished=session.auto_finished,
            answers={qid: a.selected_option for qid, a in answers.items() if a.selected_option},
        )
    else:
        # Soru çözümünde cevaplanan soruların değerlendirmesi zaten gösterildi; sayfa yenilenince geri yüklenir.
        data.update(
            mistakes_only=session.mistakes_only,
            answers={
                q.id: evaluation_result(q, _option(q, answers[q.id].selected_option))
                for q in questions
                if q.id in answers
            },
        )
    return data


def session_result(session):
    """Bitmiş oturumun sonucu: sayılar, soru soru inceleme, kavram yanılgısı özeti ve ödüller."""
    if not session.is_finished:
        raise ExamConflict("Sonuçlar oturum bittikten sonra gösterilir.")
    answers = {a.question_id: a for a in session.answers.all()}
    items = []
    misconceptions = {}
    for question in _questions(session):
        answer = answers.get(question.id)
        option = next((o for o in question.options if answer and o.key == answer.selected_option), None)
        review = evaluation_result(question, option)
        items.append({"question": public_question(question), **review, "answered": answer is not None and bool(answer.selected_option)})
        if review["misconception"]:
            tag = review["misconception"]["tag"]
            entry = misconceptions.setdefault(tag, {**review["misconception"], "count": 0, "question_ids": []})
            entry["count"] += 1
            entry["question_ids"].append(question.id)
    answered = session.correct_count + session.incorrect_count
    data = {
        **_base(session),
        "summary": {
            "total": session.question_count,
            "correct": session.correct_count,
            "incorrect": session.incorrect_count,
            "blank": session.blank_count,
            "success_rate": session.correct_count / session.question_count if session.question_count else None,
            "accuracy": session.correct_count / answered if answered else None,
        },
        "duration_used_seconds": int((session.finished_at - session.started_at).total_seconds()),
        "rewards": session.rewards or {"points": 0, "badges": [], "tasks": [], "goals": []},
        "misconceptions": sorted(misconceptions.values(), key=lambda m: -m["count"]),
        "items": items,
    }
    if isinstance(session, TimedExamSession):
        data.update(duration_seconds=session.duration_seconds, auto_finished=session.auto_finished)
    else:
        data.update(mistakes_only=session.mistakes_only)
    return data


def session_summary(session):
    """Oturum listesi için kısa özet."""
    data = {
        **_base(session),
        "correct": session.correct_count,
        "incorrect": session.incorrect_count,
        "blank": session.blank_count,
    }
    if isinstance(session, TimedExamSession):
        data["deadline"] = session.deadline
    return data
