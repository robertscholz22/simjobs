# syntax=docker/dockerfile:1

# ---- builder: resolve and install dependencies into a self-contained .venv ----
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS builder

# Take the uv binary from its own image instead of installing it with pip
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first: this layer only changes when the lockfile does.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Then the source, which changes on every commit.
COPY src ./src
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- runtime: the same base, without uv and without build caches
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Fixed uid so file ownership is predictable in Compose, ECS and Kubernetes
RUN groupadd --gid 10001 simjobs \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin simjobs

WORKDIR /app
COPY --from=builder --chown=10001:10001 /app /app

USER 10001:10001
EXPOSE 8000

# urllib, because the image doesn't have curl
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz').read()"]

ENTRYPOINT ["simjobs"]
CMD ["api"]
