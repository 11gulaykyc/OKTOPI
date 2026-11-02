from typing import Annotated, Literal, Optional

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


class Slider(StrictModel):
    """Öğrencinin değiştirebildiği bir parametre (ör. eğim `m`)."""

    name: NonEmptyStr
    label: NonEmptyStr  # $...$ LaTeX içerebilir
    min: float
    max: float
    step: float = Field(gt=0)
    value: float

    @model_validator(mode="after")
    def check_range(self):
        if self.min >= self.max:
            raise ValueError(f"Kaydırıcı '{self.name}': min, max değerinden küçük olmalıdır.")
        if not self.min <= self.value <= self.max:
            raise ValueError(f"Kaydırıcı '{self.name}': başlangıç değeri [min, max] aralığında olmalıdır.")
        return self


# Her görselleştirme türünün beklediği kaydırıcılar.
#   linear      → y = m·x + n
#   parabola    → y = a·x² + b·x + c
#   exponential → y = aˣ ve x = n noktasındaki değer
#   triangle    → A ve B iç açıları (derece); C = 180° − A − B
VISUALIZATION_SLIDERS = {
    "linear": {"m", "n"},
    "parabola": {"a", "b", "c"},
    "exponential": {"a", "n"},
    "triangle": {"A", "B"},
}


VisualizationId = Annotated[str, Field(pattern=r"^viz-(9|10|11|12)-[a-z0-9]+(-[a-z0-9]+)*$")]


class Visualization(StrictModel):
    """Konu anlatımına bağlanan etkileşimli grafik (frontend: GeometryCanvas.vue / JSXGraph)."""

    id: VisualizationId
    type: Literal["linear", "parabola", "exponential", "triangle"]
    section_id: Optional[TopicId] = None  # verilirse o bölümün içinde gösterilir
    title: NonEmptyStr
    description: Optional[NonEmptyStr] = None
    # JSXGraph sırası: [x_min, y_max, x_max, y_min]
    bounds: tuple[float, float, float, float] = (-6.0, 6.0, 6.0, -6.0)
    sliders: list[Slider] = Field(min_length=1)

    @model_validator(mode="after")
    def check_params(self):
        names = [s.name for s in self.sliders]
        if len(names) != len(set(names)):
            raise ValueError(f"{self.id}: kaydırıcı adları benzersiz olmalıdır.")
        expected = VISUALIZATION_SLIDERS[self.type]
        if set(names) != expected:
            raise ValueError(f"{self.id}: '{self.type}' türü şu kaydırıcıları bekler: {', '.join(sorted(expected))}.")
        x_min, y_max, x_max, y_min = self.bounds
        if x_min >= x_max or y_min >= y_max:
            raise ValueError(f"{self.id}: bounds [x_min, y_max, x_max, y_min] sırasında olmalıdır.")
        by_name = {s.name: s for s in self.sliders}
        if self.type == "exponential" and by_name["a"].min <= 0:
            raise ValueError(f"{self.id}: üstel fonksiyonda taban (a) pozitif olmalıdır.")
        if self.type == "triangle":
            a, b = by_name["A"], by_name["B"]
            if a.min <= 0 or b.min <= 0:
                raise ValueError(f"{self.id}: üçgen açıları 0°'den büyük olmalıdır.")
            if a.value + b.value >= 180:
                raise ValueError(f"{self.id}: başlangıçta A + B < 180° olmalıdır.")
        return self


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
        viz_ids = [v.id for v in self.visualizations]
        if len(viz_ids) != len(set(viz_ids)):
            raise ValueError(f"{self.id}: görselleştirme kimlikleri benzersiz olmalıdır.")
        for viz in self.visualizations:
            if viz.section_id and viz.section_id not in ids:
                raise ValueError(f"{self.id}: görselleştirme '{viz.id}' var olmayan bölüme ({viz.section_id}) bağlı.")
        if not self.theme_id.startswith(f"th-{self.grade}-"):
            raise ValueError(f"{self.id}: tema kimliği sınıf düzeyiyle uyuşmuyor.")
        return self
