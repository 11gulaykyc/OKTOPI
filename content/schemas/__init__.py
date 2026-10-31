"""OKTOPİ içerik şemaları (Pydantic v2).

`content/` altındaki tüm JSON dosyaları bu modellerle doğrulanır. Backend bu modülü
`from content.schemas import ...` şeklinde içe aktarır.
"""

from .curriculum import GradeCurriculumSchema, LearningOutcome, SubtopicRef, ThemeSchema, TopicRef
from .oyss import OyssSchema
from .question import QuestionFileSchema, QuestionOption, QuestionSchema
from .topic import TopicSchema

__all__ = [
    "GradeCurriculumSchema",
    "LearningOutcome",
    "OyssSchema",
    "QuestionFileSchema",
    "QuestionOption",
    "QuestionSchema",
    "SubtopicRef",
    "ThemeSchema",
    "TopicRef",
    "TopicSchema",
]
