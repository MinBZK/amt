from fastapi.templating import Jinja2Templates
from jinja2 import Environment

env = Environment(
    autoescape=True,
)
templates = Jinja2Templates(directory="tad/site/templates/", env=env)
