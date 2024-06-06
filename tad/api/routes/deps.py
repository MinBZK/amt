from fastapi.templating import Jinja2Templates
from jinja2 import Environment

from tad.core.config import settings

env = Environment(
    autoescape=True,
)
templates = Jinja2Templates(directory=settings.TEMPLATE_DIR, env=env)
