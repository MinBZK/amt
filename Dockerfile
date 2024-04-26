ARG PYTHON_VERSION=3.11.7-slim

FROM  --platform=$BUILDPLATFORM python:${PYTHON_VERSION} as project-base

LABEL maintainer=ai-validatie@minbzk.nl \
      organization=MinBZK \
      license=EUPL-1.2 \
      io.docker.minbzk.name=python-project-template

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME='/usr/local'

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN  curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app/
COPY ./poetry.lock ./pyproject.toml ./

RUN poetry install --without dev,test
ENV PATH="/app/.venv/bin:$PATH"

FROM project-base as development

COPY . .
RUN poetry install

FROM development AS lint

RUN ruff check
RUN ruff format --check

FROM development AS test
RUN coverage run --rcfile ./pyproject.toml -m pytest ./tests
RUN coverage report --fail-under 95

FROM project-base as production

COPY ./python_project /app/python_project

# change this to a usefull command
CMD ["python", "-m", "python_project" ]
