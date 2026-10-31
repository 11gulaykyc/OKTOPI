from typing import Optional

from pydantic import Field, model_validator

from .common import Grade, LearningOutcomeCode, NonEmptyStr, StrictModel, ThemeId, TopicId, Version


class LearningOutcome(StrictModel):
    code: LearningOutcomeCode
    text: NonEmptyStr


class SubtopicRef(StrictModel):
    id: TopicId
    title: NonEmptyStr


class TopicRef(StrictModel):
    id: TopicId
    title: NonEmptyStr
    learning_outcomes: list[LearningOutcome] = Field(default_factory=list)
    subtopics: list[SubtopicRef] = Field(default_factory=list)
    # Konu anlatımı JSON dosyası (grade-X/topics/ altına göre). Henüz yazılmadıysa null.
    content_file: Optional[str] = None


class ThemeSchema(StrictModel):
    id: ThemeId
    order: int = Field(ge=1)
    title: NonEmptyStr
    description: str = ""
    topics: list[TopicRef] = Field(min_length=1)


class GradeCurriculumSchema(StrictModel):
    """`curriculum/grade-X/index.json`: bir sınıfın tema → konu → alt konu ağacı."""

    grade: Grade
    version: Version
    title: NonEmptyStr
    program: NonEmptyStr
    themes: list[ThemeSchema] = Field(min_length=1)

    @model_validator(mode="after")
    def check_ids(self):
        prefix_theme = f"th-{self.grade}-"
        prefix_topic = f"top-{self.grade}-"
        seen = set()
        for theme in self.themes:
            if not theme.id.startswith(prefix_theme):
                raise ValueError(f"Tema kimliği '{theme.id}' {self.grade}. sınıfa ait değil.")
            for topic in theme.topics:
                for item_id in [topic.id, *(s.id for s in topic.subtopics)]:
                    if not item_id.startswith(prefix_topic):
                        raise ValueError(f"Kimlik '{item_id}' {self.grade}. sınıfa ait değil.")
                    if item_id in seen:
                        raise ValueError(f"Kimlik '{item_id}' birden fazla kez tanımlanmış.")
                    seen.add(item_id)
                for outcome in topic.learning_outcomes:
                    if not outcome.code.startswith(f"MAT.{self.grade}."):
                        raise ValueError(f"Kazanım '{outcome.code}' {self.grade}. sınıfa ait değil.")
        orders = [t.order for t in self.themes]
        if len(orders) != len(set(orders)):
            raise ValueError("Tema sıra numaraları (order) benzersiz olmalıdır.")
        return self

    def all_ids(self):
        """Tüm konu ve alt konu kimlikleri."""
        ids = set()
        for theme in self.themes:
            for topic in theme.topics:
                ids.add(topic.id)
                ids.update(s.id for s in topic.subtopics)
        return ids
