import hashlib
import os
import sys
import urllib
from functools import lru_cache
from os import PathLike
from pathlib import Path
from typing import NamedTuple
from urllib.parse import ParseResult, urlencode

from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from amt.core.exceptions import AMTNotFound, AMTOnlyStatic


class StaticFilesCache(StaticFiles):
    def __init__(
        self,
        *,
        directory: PathLike[str] | None = None,
        packages: list[str | tuple[str, str]] | None = None,
        html: bool = False,
        check_dir: bool = True,
        follow_symlink: bool = False,
        immutable_cache_control: str = "public, max-age=31536000, immutable",
        temporary_cache_control: str = "public, max-age=3600, must-revalidate",
    ) -> None:
        self.immutable_cache_control = immutable_cache_control
        self.temporary_cache_control = temporary_cache_control
        super().__init__(
            directory=directory, packages=packages, html=html, check_dir=check_dir, follow_symlink=follow_symlink
        )

    def file_response(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        full_path: PathLike,  # pyright: ignore
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        resp: Response = super().file_response(
            full_path=full_path,  # pyright: ignore [reportUnknownArgumentType]
            stat_result=stat_result,
            scope=scope,
            status_code=status_code,
        )
        if b"etag=" in scope["query_string"]:
            resp.headers.setdefault("Cache-Control", self.immutable_cache_control)
        else:
            resp.headers.setdefault("Cache-Control", self.temporary_cache_control)
        return resp


class URLComponents(NamedTuple):
    schema: str
    netloc: str
    url: str
    path: str
    query: str
    fragment: str


@lru_cache(maxsize=0 if "pytest" in sys.modules else 1000)
def url_for_cache(name: str, /, **path_params: str) -> str:
    if name != "static":
        raise AMTOnlyStatic()

    url_parts: ParseResult = urllib.parse.urlparse(path_params["path"])  # type: ignore
    if url_parts.scheme or url_parts.hostname:  # type: ignore
        raise AMTOnlyStatic()

    query_list: dict[str, str] = dict(x.split("=") for x in url_parts.query.split("&")) if url_parts.query else {}  # type: ignore
    resolved_url_path: str = "/" + name + "/" + url_parts.path  # type: ignore
    _, stat_result = static_files.lookup_path(url_parts.path)  # type: ignore
    if not stat_result:
        raise AMTNotFound()

    etag_base = str(stat_result.st_mtime) + "-" + str(stat_result.st_size)
    etag = hashlib.md5(etag_base.encode(), usedforsecurity=False).hexdigest()
    query_list["etag"] = etag

    return_url = urllib.parse.urlunparse(  # type: ignore
        URLComponents("", "", resolved_url_path, "", urlencode(query_list), "")
    )
    return str(return_url)  # type: ignore


static_files = StaticFilesCache(directory=Path("amt/site/static"))
