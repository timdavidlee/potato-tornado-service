# syntax=docker/dockerfile:1
# uv image bundling Python 3.14. Build with SSH forwarding so the private
# `potato-tornado` git dependency resolves:  docker build --ssh default .
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new"

# git + ssh client are needed to fetch the private dependency over SSH.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Resolve dependencies first for layer caching (project code excluded).
COPY pyproject.toml uv.lock ./
RUN --mount=type=ssh uv sync --frozen --no-install-project --no-dev

# Then install the app itself.
COPY . .
RUN --mount=type=ssh uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "potato_tornado_service.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
