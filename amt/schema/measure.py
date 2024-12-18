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
    links: list[str] = Field(default=[])
    files: list[str] = Field(default=[])
    version: str
    accountable_persons: list[Person] | None = Field(default=[])
    reviewer_persons: list[Person] | None = Field(default=[])
    responsible_persons: list[Person] | None = Field(default=[])

    def update(
        self,
        state: str | None,
        value: str | None,
        links: list[str] | None,
        new_files: list[str] | None,
        responsible_persons: list[Person] | None,
        reviewer_persons: list[Person] | None,
        accountable_persons: list[Person] | None,
    ) -> None:
        if state:
            self.state = state

        if value:
            self.value = value

        self.links = [link for link in links if link] if links else []

        if new_files:
            self.files.extend(new_files)

        self.responsible_persons = responsible_persons
        self.reviewer_persons = reviewer_persons
        self.accountable_persons = accountable_persons


class Measure(MeasureBase):
    name: str
    schema_version: str
    description: str
    links: list[str] = Field(default=[])
    url: str


class ExtendedMeasureTask(MeasureTask):
    name: str
    description: str
