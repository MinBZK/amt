from pydantic import Field

from amt.schema.shared import BaseModel


class MeasureBase(BaseModel):
    urn: str


class Person(BaseModel):
    name: str
    uuid: str


class MeasureTask(MeasureBase):
    state: str = Field(default="")
    value: str = Field(default="")
    links: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    version: str
    accountable_persons: list[Person] | None = Field(default_factory=list)
    reviewer_persons: list[Person] | None = Field(default_factory=list)
    responsible_persons: list[Person] | None = Field(default_factory=list)
    lifecycle: list[str] = Field(default_factory=list)

    def update(
        self,
        state: str | None = None,
        value: str | None = None,
        links: list[str] | None = None,
        new_files: list[str] | None = None,
        responsible_persons: list[Person] | None = None,
        reviewer_persons: list[Person] | None = None,
        accountable_persons: list[Person] | None = None,
    ) -> None:
        if state:
            self.state = state

        if value:
            self.value = value

        self.links = [link for link in links if link] if links else []

        if new_files:
            self.files.extend(new_files)

        if responsible_persons is not None:
            self.responsible_persons = responsible_persons

        if reviewer_persons is not None:
            self.reviewer_persons = reviewer_persons

        if accountable_persons is not None:
            self.accountable_persons = accountable_persons


class Measure(MeasureBase):
    name: str
    schema_version: str
    description: str
    links: list[str] = Field(default_factory=list)
    url: str
    lifecycle: list[str] = Field(default_factory=list)


class ExtendedMeasureTask(MeasureTask):
    name: str
    description: str
