from pydantic import Field

from amt.schema.shared import BaseModel


class MeasureBase(BaseModel):
    urn: str


class MeasureTask(MeasureBase):
    state: str = Field(default="")
    value: str = Field(default="")
    links: list[str] = Field(default=[])
    files: list[str] = Field(default=[])
    version: str

    def update(
        self,
        state: str | None,
        value: str | None,
        links: list[str] | None,
        new_files: list[str] | None,
    ) -> None:
        if state:
            self.state = state

        if value:
            self.value = value

        self.links = [link for link in links if link] if links else []

        if new_files:
            self.files.extend(new_files)


class Measure(MeasureBase):
    name: str
    schema_version: str
    description: str
    links: list[str] = Field(default=[])
    url: str


class ExtendedMeasureTask(MeasureTask):
    name: str
    description: str
