FROM ghcr.io/astral-sh/uv:0.5 AS uv

FROM python:3.12-slim-bookworm AS builder

COPY --from=uv /uv /uvx /bin/
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-workspace --no-dev

COPY ./app ./app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get upgrade -y libgnutls30 \
    && rm -rf /var/lib/apt/lists/*

ARG GIT_SHA=local
ENV SENTRY_RELEASE=$GIT_SHA \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

COPY ./data ./data
COPY ./alembic.ini .
COPY ./alembic     ./alembic
COPY ./scripts     ./scripts
COPY ./app         ./app

RUN rm -rf \
    /usr/local/lib/python3.12/site-packages/pip* \
    /usr/local/lib/python3.12/site-packages/setuptools* \
    /usr/local/lib/python3.12/site-packages/pkg_resources* \
    /usr/local/lib/python3.12/site-packages/wheel* \
    /usr/local/bin/pip*

RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app/uploads

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

CMD ["/app/scripts/start.sh"]
