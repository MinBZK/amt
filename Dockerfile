ARG PYTHON_VERSION=3.11.7-slim

FROM  --platform=$BUILDPLATFORM python:${PYTHON_VERSION} AS project-base

LABEL maintainer=ai-validatie@minbzk.nl \
    organization=MinBZK \
    license=EUPL-1.2 \
    org.opencontainers.image.description="Transparency of Algorithmic Decision making" \
    org.opencontainers.image.source=https://github.com/MinBZK/tad \
    org.opencontainers.image.licenses=EUPL-1.2

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME='/usr/local'

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN  curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app/
COPY ./poetry.lock ./pyproject.toml ./

RUN poetry install --without dev,test
ENV PATH="/app/.venv/bin:$PATH"

FROM project-base AS development

COPY ./tad/ ./tad/
COPY ./tests/ ./tests/
COPY ./script/ ./script/
COPY ./README.md ./README.md
RUN poetry install

FROM development AS lint

RUN ruff check
RUN ruff format --check
RUN pyright

FROM development AS test
RUN coverage run -m pytest
RUN coverage report

FROM project-base AS production

RUN groupadd tad && \
    adduser --uid 100 --system --ingroup tad tad

#todo(berry): create log folder so permissions can be set to root:root
# currenlt problem is that i could not get the logger to accept a path in the filerotate handler
RUN chown tad:tad /app/

USER tad

COPY --chown=root:root --chmod=755 ./tad /app/tad
COPY --chown=root:root --chmod=755 alembic.ini /app/alembic.ini
COPY --chown=root:root --chmod=755 prod.env /app/.env
COPY --chown=root:root --chmod=755 LICENSE /app/LICENSE
COPY --chown=tad:tad --chmod=755 docker-entrypoint.sh /app/docker-entrypoint.sh

ENV PYTHONPATH=/app/
WORKDIR /app/

ENV PATH="/app/:$PATH"

CMD [ "docker-entrypoint.sh" ]
