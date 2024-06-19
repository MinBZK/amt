from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment

from tad.core.config import VERSION


def version_context_processor(request: Request):
    return {"version": VERSION}


env = Environment(
    autoescape=True,
)
templates = Jinja2Templates(directory="tad/site/templates/", context_processors=[version_context_processor], env=env)
