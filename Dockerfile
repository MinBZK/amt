ARG PYTHON_VERSION=3.12.7-slim
ARG NVM_VERSION=0.40.0

FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION} AS project-base
ARG NVM_VERSION
# Set NVM_VERSION again to make sure it's properly passed to this stage
ENV NVM_VERSION=${NVM_VERSION}

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
    POETRY_HOME='/usr/local'

# Install dependencies in a single layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 -

# Copy dependency files first for better caching
WORKDIR /app/
COPY ./poetry.lock ./pyproject.toml ./

# Install Python dependencies
RUN poetry install --without dev,test

# Copy node-related config files
COPY ./package-lock.json ./package.json .nvmrc ./
COPY ./webpack.config.js ./webpack.config.prod.js ./
COPY ./tsconfig.json ./eslint.config.mjs ./
COPY ./jest.config.ts ./

# Install Node.js directly instead of using NVM
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    node --version && \
    npm --version

# Install Node.js dependencies
RUN npm ci

# Set Python path
ENV PATH="/app/.venv/bin:$PATH"

# Development stage with test dependencies
FROM project-base AS development

COPY amt/ ./amt/
COPY ./tests/ ./tests/
COPY ./script/ ./script/
COPY ./README.md ./README.md
RUN poetry install

# Lint stage
FROM development AS lint
COPY ./.prettierrc ./.prettierignore ./
RUN ruff format --check
RUN npm run prettier:check
RUN ruff check
RUN npm run lint
RUN pyright

# Test stage
FROM development AS test

COPY ./example/ ./example/
COPY ./resources/ ./resources/
RUN npm run build

# Production stage
FROM project-base AS production

# Create non-root user and set permissions
RUN groupadd amt && \
    adduser --uid 100 --system --ingroup amt amt \
    && mkdir -p ./amt/site/static/dist/ ./amt/site/templates/layouts/ \
    && chown amt:amt /app/ \
    && chown amt:amt -R ./amt/site/static/dist/ \
    && chown amt:amt -R ./amt/site/templates/layouts/

# Copy application code and config files
COPY --chown=root:root --chmod=755 amt /app/amt
COPY --chown=root:root --chmod=755 alembic.ini /app/alembic.ini
COPY --chown=root:root --chmod=755 prod.env /app/.env
COPY --chown=root:root --chmod=755 resources /app/resources
COPY --chown=root:root --chmod=755 LICENSE /app/LICENSE
COPY --chown=amt:amt --chmod=755 docker-entrypoint.sh /app/docker-entrypoint.sh

# Build frontend assets as amt user
USER amt
RUN npm run build

# Set environment and working directory
ENV PYTHONPATH=/app/
WORKDIR /app/
ENV PATH="/app/:$PATH"

CMD [ "docker-entrypoint.sh" ]
