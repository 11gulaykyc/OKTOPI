from typing import Literal, Optional

from pydantic import Field, model_validator

from .common import (
    Grade,
    LearningOutcomeCode,
    MisconceptionTag,
    NonEmptyStr,
    QuestionId,
    StrictModel,
    TopicId,
    Version,
)


class QuestionOption(StrictModel):
    key: Literal["A", "B", "C", "D", "E"]
    text: NonEmptyStr
    is_correct: bool
    misconception_tag: Optional[MisconceptionTag]
    misconception_detail: Optional[NonEmptyStr]
    recommended_subtopic_id: Optional[TopicId]

    @model_validator(mode="after")
    def check_misconception_fields(self):
        misconception = (self.misconception_tag, self.misconception_detail, self.recommended_subtopic_id)
        if self.is_correct and any(v is not None for v in misconception):
            raise ValueError(
                f"Doğru şık ({self.key}) için misconception_tag, misconception_detail ve "
                "recommended_subtopic_id null olmalıdır."
            )
        if not self.is_correct and any(v is None for v in misconception):
            raise ValueError(
                f"Yanlış şık ({self.key}) için misconception_tag, misconception_detail ve "
                "recommended_subtopic_id zorunludur."
            )
        return self


class QuestionSchema(StrictModel):
    id: QuestionId
    version: Version
    grade: Grade
    topic_id: TopicId
    topic: NonEmptyStr
    subtopic_id: TopicId
    subtopic: NonEmptyStr
    learning_outcome: LearningOutcomeCode
    difficulty: Literal["easy", "medium", "hard"]
    question_text: NonEmptyStr
    options: list[QuestionOption] = Field(min_length=2, max_length=5)
    step_by_step_solution: NonEmptyStr

    @model_validator(mode="after")
    def check_consistency(self):
        keys = [o.key for o in self.options]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{self.id}: şık harfleri benzersiz olmalıdır.")
        if keys != sorted(keys) or keys[0] != "A":
            raise ValueError(f"{self.id}: şıklar A'dan başlayarak sıralı olmalıdır.")
        correct = [o.key for o in self.options if o.is_correct]
        if len(correct) != 1:
            raise ValueError(f"{self.id}: tam olarak bir doğru şık olmalıdır (bulunan: {len(correct)}).")
        texts = [o.text for o in self.options]
        if len(texts) != len(set(texts)):
            raise ValueError(f"{self.id}: aynı metne sahip iki şık var.")
        if not self.id.startswith(f"q-{self.grade}-"):
            raise ValueError(f"{self.id}: kimlik sınıf düzeyiyle ({self.grade}) uyuşmuyor.")
        for item_id in (self.topic_id, self.subtopic_id):
            if not item_id.startswith(f"top-{self.grade}-"):
                raise ValueError(f"{self.id}: '{item_id}' {self.grade}. sınıfa ait değil.")
        return self

    @property
    def correct_option(self):
        return next(o for o in self.options if o.is_correct)


class QuestionFileSchema(StrictModel):
    """`questions/grade-X/<konu>.json`: bir konuya ait soru listesi."""

    version: Version
    grade: Grade
    topic_id: TopicId
    questions: list[QuestionSchema] = Field(min_length=1)

    @model_validator(mode="after")
    def check_questions_belong_here(self):
        for q in self.questions:
            if q.grade != self.grade or q.topic_id != self.topic_id:
                raise ValueError(f"{q.id}: dosyanın sınıf/konu bilgisiyle uyuşmuyor.")
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Dosyada tekrar eden soru kimliği var.")
        return self
