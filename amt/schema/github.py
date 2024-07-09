from pydantic import BaseModel, HttpUrl, RootModel


class Links(BaseModel):
    self: HttpUrl
    git: HttpUrl
    html: HttpUrl


class ContentItem(BaseModel):
    name: str
    path: str
    sha: str
    size: int
    url: HttpUrl
    html_url: HttpUrl
    git_url: HttpUrl
    download_url: HttpUrl
    type: str
    _links: Links


class RepositoryContent(RootModel[list[ContentItem]]):
    pass
