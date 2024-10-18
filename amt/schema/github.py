from pydantic import BaseModel, Field, HttpUrl, RootModel


class Links(BaseModel):
    self: HttpUrl
    git: HttpUrl | None = Field(default=None)
    html: HttpUrl | None = Field(default=None)


class ContentItem(BaseModel):
    name: str
    urn: str
    path: str
    sha: str | None = Field(default=None)
    size: int
    url: HttpUrl | None = Field(default=None)
    html_url: HttpUrl | None = Field(default=None)
    git_url: HttpUrl | None = Field(default=None)
    download_url: HttpUrl
    type: str
    _links: Links


class RepositoryContent(RootModel[list[ContentItem]]):
    pass
