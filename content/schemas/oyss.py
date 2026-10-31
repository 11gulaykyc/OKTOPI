from datetime import date
from typing import Literal, Optional

from pydantic import Field, model_validator

from .common import Grade, NonEmptyStr, StrictModel, TopicId, Version


class OyssExam(StrictModel):
    grade: Grade
    term: Literal[1, 2]
    exam_no: int = Field(ge=1, le=3)
    period_label: NonEmptyStr
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    topic_ids: list[TopicId] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Sınav bitiş tarihi başlangıçtan önce olamaz.")
        return self


class OyssTip(StrictModel):
    title: NonEmptyStr
    body: NonEmptyStr


class OyssFaq(StrictModel):
    question: NonEmptyStr
    answer: NonEmptyStr


class OyssSchema(StrictModel):
    """`curriculum/oyss/oyss.json`: Ortak Yazılı Sınav Sistemi bilgilendirme içeriği."""

    version: Version
    academic_year: NonEmptyStr
    title: NonEmptyStr
    intro: NonEmptyStr
    about: list[NonEmptyStr] = Field(min_length=1)
    # Takvim resmî MEB duyurusuyla doğrulanmadıysa false kalır ve arayüzde uyarı gösterilir.
    calendar_is_official: bool
    calendar_source: Optional[str] = None
    calendar: list[OyssExam] = Field(default_factory=list)
    preparation_tips: list[OyssTip] = Field(default_factory=list)
    faq: list[OyssFaq] = Field(default_factory=list)
