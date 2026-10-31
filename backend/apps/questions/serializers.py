"""Soru verisinin istemciye giden biçimi.

KURAL: Cevap anahtarı (is_correct), kavram yanılgısı alanları ve çözüm, değerlendirme
tamamlanmadan istemciye gönderilmez. Bu modül yalnızca izin verilen alanları dışarı açar.
"""

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
