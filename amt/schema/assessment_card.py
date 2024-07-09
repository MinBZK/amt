from datetime import datetime

from pydantic import (
    BaseModel,
    Field,  # pyright: ignore [reportUnknownMemberType]
)


class AssessmentAuthor(BaseModel):
    name: str = Field(default=None)


class AssessmentContent(BaseModel):
    question: str = Field(default=None)
    urn: str = Field(default=None)
    answer: str = Field(default=None)
    remarks: str = Field(default=None)
    authors: list[AssessmentAuthor] = Field(default=[])
    timestamp: datetime | None = Field(default=None)


class AssessmentCard(BaseModel):
    name: str = Field(default=None)
    urn: str = Field(default=None)
    date: datetime = Field(default=None)
    contents: list[AssessmentContent] = Field(default=[])
