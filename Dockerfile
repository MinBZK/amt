ARG PYTHON_VERSION=3.11.7-slim
ARG NVM_VERSION=0.40.0

FROM  --platform=$BUILDPLATFORM python:${PYTHON_VERSION} AS project-base
ARG NVM_VERSION

LABEL maintainer=ai-validatie@minbzk.nl \
    organization=MinBZK \
    license=EUPL-1.2 \
    org.opencontainers.image.description="Transparency of Algorithmic Decision making" \
    org.opencontainers.image.source=https://github.com/MinBZK/amt \
    org.opencontainers.image.licenses=EUPL-1.2

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME='/usr/local' \
    NVM_DIR=/usr/local/nvm

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN  curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app/
COPY ./poetry.lock ./pyproject.toml ./
COPY ./package-lock.json ./package.json .nvmrc ./
COPY ./webpack.config.js ./webpack.config.prod.js ./
COPY ./tsconfig.json ./eslint.config.mjs ./
COPY ./jest.config.ts ./

RUN mkdir -p $NVM_DIR && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh | bash

RUN . ~/.bashrc && nvm install && nvm use

RUN poetry install --without dev,test
RUN . "$NVM_DIR/nvm.sh" && npm install
ENV PATH="$NVM_DIR/versions/node/v20.16.0/bin:$PATH"
ENV PATH="/app/.venv/bin:$PATH"

FROM project-base AS development

COPY amt/ ./amt/
COPY ./tests/ ./tests/
COPY ./script/ ./script/
COPY ./README.md ./README.md
RUN poetry install

FROM development AS lint
COPY ./.prettierrc ./.prettierignore ./
RUN ruff format --check
RUN npm run prettier:check
RUN ruff check
RUN npm run lint
RUN pyright

FROM development AS test

COPY ./example/ ./example/
RUN npm run build

FROM project-base AS production


RUN groupadd amt && \
    adduser --uid 100 --system --ingroup amt amt

#todo(berry): create log folder so permissions can be set to root:root
# currenlt problem is that i could not get the logger to accept a path in the filerotate handler
RUN chown amt:amt /app/

USER amt

COPY --chown=root:root --chmod=755 amt /app/amt
COPY --chown=root:root --chmod=755 alembic.ini /app/alembic.ini
COPY --chown=root:root --chmod=755 prod.env /app/.env
COPY --chown=root:root --chmod=755 LICENSE /app/LICENSE
COPY --chown=amt:amt --chmod=755 docker-entrypoint.sh /app/docker-entrypoint.sh
USER root
RUN mkdir -p ./amt/site/static/dist/
RUN chown amt:amt -R ./amt/site/static/dist/
RUN chown amt:amt -R ./amt/site/templates/layouts/
USER amt
RUN npm run build

ENV PYTHONPATH=/app/
WORKDIR /app/

ENV PATH="/app/:$PATH"

CMD [ "docker-entrypoint.sh" ]
