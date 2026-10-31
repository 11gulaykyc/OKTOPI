from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Grade = Literal[9, 10, 11, 12]
Version = Annotated[str, Field(pattern=r"^\d+\.\d+$")]
NonEmptyStr = Annotated[str, Field(min_length=1)]

# Konu ve alt konu kimlikleri: top-<sınıf>-<kısa-ad>[-<alt-ad>...]
TopicId = Annotated[str, Field(pattern=r"^top-(9|10|11|12)-[a-z0-9]+(-[a-z0-9]+)*$")]
ThemeId = Annotated[str, Field(pattern=r"^th-(9|10|11|12)-\d+$")]
QuestionId = Annotated[str, Field(pattern=r"^q-(9|10|11|12)-[a-z0-9]+-\d{3}$")]
LearningOutcomeCode = Annotated[str, Field(pattern=r"^MAT\.(9|10|11|12)\.\d+\.\d+$")]
MisconceptionTag = Annotated[str, Field(pattern=r"^MISC_[A-Z0-9]+(_[A-Z0-9]+)*$")]


class StrictModel(BaseModel):
    """Bilinmeyen alanları reddeder; içerik yazım hataları sessizce kaybolmasın."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
