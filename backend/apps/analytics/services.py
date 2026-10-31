from .models import MisconceptionLog


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
