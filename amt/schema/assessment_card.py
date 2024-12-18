from datetime import datetime

from pydantic import Field  # pyright: ignore [reportUnknownMemberType]

from amt.schema.shared import BaseModel


class AssessmentAuthor(BaseModel):
    name: str | None = Field(default=None)


class AssessmentContent(BaseModel):
    question: str | None = Field(default=None)
    urn: str | None = Field(default=None)
    answer: str | None = Field(default=None)
    remarks: str | None = Field(default=None)
    authors: list[AssessmentAuthor] = Field(default=[])
    timestamp: datetime | None = Field(default=None)


class AssessmentCard(BaseModel):
    name: str | None = Field(default=None)
    urn: str | None = Field(default=None)
    date: datetime | None = Field(default=None)
    contents: list[AssessmentContent] = Field(default=[])
