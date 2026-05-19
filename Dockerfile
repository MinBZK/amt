ARG PYTHON_VERSION=3.12-slim
ARG NVM_VERSION=0.40.0

FROM  --platform=$BUILDPLATFORM python:${PYTHON_VERSION} AS project-base
ARG NVM_VERSION

LABEL maintainer=ai-validatie@minbzk.nl \
    organization=MinBZK \
    license=EUPL-1.2 \
    org.opencontainers.image.description="Algoritm Management Toolkit" \
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

# Upgrade OS packages so base-image CVEs are patched on every rebuild,
# not frozen at the digest the python:slim tag pointed to.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends curl libpq-dev \
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

RUN poetry install --without dev,test --no-root
RUN . "$NVM_DIR/nvm.sh" && npm ci
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
COPY ./resources/ ./resources/
RUN npm run build

# Builder stage: produces the webpack assets that the production image needs.
# Node, npm and nvm live here only and never reach the runtime image.
FROM project-base AS asset-builder
COPY amt/ ./amt/
RUN npm run build

FROM python:${PYTHON_VERSION} AS production

LABEL maintainer=ai-validatie@minbzk.nl \
    organization=MinBZK \
    license=EUPL-1.2 \
    org.opencontainers.image.description="Algoritm Management Toolkit" \
    org.opencontainers.image.source=https://github.com/MinBZK/amt \
    org.opencontainers.image.licenses=EUPL-1.2

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Same OS upgrade as the base; the runtime image is built FROM the clean
# python:slim and only carries libpq for psycopg, no build toolchain.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd amt && \
    adduser --uid 100 --system --ingroup amt amt

#todo(berry): create log folder so permissions can be set to root:root
# current problem is that i could not get the logger to accept a path in the filerotate handler
RUN mkdir -p /app/ && chown amt:amt /app/

# Python environment built by poetry in project-base, no node/npm/nvm.
COPY --from=project-base --chown=amt:amt /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/

USER amt

COPY --chown=root:root --chmod=755 amt /app/amt
COPY --chown=root:root --chmod=755 alembic.ini /app/alembic.ini
COPY --chown=root:root --chmod=755 prod.env /app/.env
COPY --chown=root:root --chmod=755 resources /app/resources
COPY --chown=root:root --chmod=755 LICENSE /app/LICENSE
COPY --chown=amt:amt --chmod=755 docker-entrypoint.sh /app/docker-entrypoint.sh

# Webpack output from the asset-builder stage: the compiled dist bundle and
# the generated base layout. No node_modules end up in the runtime image.
COPY --from=asset-builder --chown=amt:amt /app/amt/site/static/dist/ /app/amt/site/static/dist/
COPY --from=asset-builder --chown=amt:amt /app/amt/site/templates/layouts/ /app/amt/site/templates/layouts/

ENV PYTHONPATH=/app/
ENV PATH="/app/:$PATH"

# No curl in this image; the interpreter is always present.
# start-period covers a cold start: alembic runs all migrations in the
# entrypoint before uvicorn binds, which can take well over a minute on a
# slow runner or a large migration history.
HEALTHCHECK --interval=10s --timeout=5s --start-period=120s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health/live').status==200 else 1)"]

CMD [ "docker-entrypoint.sh" ]
