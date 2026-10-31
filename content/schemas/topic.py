from typing import Any, Optional

from pydantic import Field, model_validator

from .common import Grade, NonEmptyStr, QuestionId, StrictModel, ThemeId, TopicId, Version


class Formula(StrictModel):
    label: NonEmptyStr
    latex: NonEmptyStr


class WorkedExample(StrictModel):
    title: NonEmptyStr
    problem: NonEmptyStr
    steps: list[NonEmptyStr] = Field(min_length=1)
    answer: NonEmptyStr


class TopicSection(StrictModel):
    # Bölüm kimliği, müfredat ağacındaki bir alt konu kimliğidir (yönlendirme hedefi).
    id: TopicId
    title: NonEmptyStr
    body: NonEmptyStr  # Markdown + $...$ / $$...$$ LaTeX
    formulas: list[Formula] = Field(default_factory=list)
    examples: list[WorkedExample] = Field(default_factory=list)
    tip: Optional[str] = None
    common_mistakes: list[NonEmptyStr] = Field(default_factory=list)


class Visualization(StrictModel):
    """Faz 4 etkileşimli geometri modülü için parametreler (şimdilik serbest yapı)."""

    id: NonEmptyStr
    type: NonEmptyStr
    section_id: Optional[TopicId] = None
    params: dict[str, Any] = Field(default_factory=dict)


class TopicSchema(StrictModel):
    """`curriculum/grade-X/topics/<konu>.json`: bir konunun anlatımı."""

    id: TopicId
    version: Version
    grade: Grade
    theme_id: ThemeId
    title: NonEmptyStr
    summary: NonEmptyStr
    estimated_minutes: int = Field(ge=1, le=240)
    learning_objectives: list[NonEmptyStr] = Field(min_length=1)
    sections: list[TopicSection] = Field(min_length=1)
    reinforcement_question_ids: list[QuestionId] = Field(default_factory=list)
    visualizations: list[Visualization] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_ids(self):
        ids = [s.id for s in self.sections]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.id}: bölüm kimlikleri benzersiz olmalıdır.")
        if not self.theme_id.startswith(f"th-{self.grade}-"):
            raise ValueError(f"{self.id}: tema kimliği sınıf düzeyiyle uyuşmuyor.")
        return self
