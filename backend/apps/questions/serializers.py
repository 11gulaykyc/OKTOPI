"""Soru verisinin istemciye giden biçimi.

KURAL: Cevap anahtarı (is_correct), kavram yanılgısı alanları ve çözüm, değerlendirme
tamamlanmadan istemciye gönderilmez. Bu modül yalnızca izin verilen alanları dışarı açar.
"""

from apps.curriculum.content_loader import get_repository

PUBLIC_QUESTION_FIELDS = (
    "id",
    "version",
    "grade",
    "topic_id",
    "topic",
    "subtopic_id",
    "subtopic",
    "learning_outcome",
    "difficulty",
    "question_text",
)
PUBLIC_OPTION_FIELDS = ("key", "text")


def public_question(question):
    data = {name: getattr(question, name) for name in PUBLIC_QUESTION_FIELDS}
    data["options"] = [{name: getattr(o, name) for name in PUBLIC_OPTION_FIELDS} for o in question.options]
    return data


def _recommendation(target_id):
    """Önerilen alt konu (veya konu) kimliğini, yönlendirme için konu + başlık bilgisine çevirir."""
    repo = get_repository()
    topic_id = repo.subtopic_parent.get(target_id, target_id)
    entry = repo.topic_ref(topic_id)
    if not entry:
        return None
    _, _, ref = entry
    title = next((s.title for s in ref.subtopics if s.id == target_id), ref.title)
    return {"topic_id": topic_id, "section_id": target_id if target_id != topic_id else None, "title": title}


def evaluation_result(question, option, first_try=None):
    """Cevap gönderildikten SONRA dönen değerlendirme: doğru şık, çözüm ve (yanlışsa) kavram yanılgısı.

    `option` None ise soru boş bırakılmıştır (süreli test sonucu).
    """
    correct = next(o for o in question.options if o.is_correct)
    result = {
        "question_id": question.id,
        "selected_option": option.key if option else "",
        "is_correct": bool(option and option.is_correct),
        "correct_option": correct.key,
        "step_by_step_solution": question.step_by_step_solution,
        "first_try": first_try,
        "misconception": None,
    }
    if option and not option.is_correct and option.misconception_tag:
        result["misconception"] = {
            "tag": option.misconception_tag,
            "detail": option.misconception_detail,
            "recommended": _recommendation(option.recommended_subtopic_id) if option.recommended_subtopic_id else None,
        }
    return result
