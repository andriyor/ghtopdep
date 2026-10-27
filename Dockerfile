FROM python:3.10-alpine

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /bin/uv

WORKDIR /app

# Install build dependencies (gcc, etc.)
RUN apk update \
    && apk --no-cache --update add build-base libffi-dev openssl-dev

# Prevent Python from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Turn off stdout/stderr buffering to make output appear in real time
ENV PYTHONUNBUFFERED 1
ENV UV_LINK_MODE=copy

# Install dependencies first to leverage Docker layer caching
ADD uv.lock pyproject.toml ./

RUN uv sync --locked --no-dev --no-install-project

# After dependencies are installed, copy the rest of the code
ADD . .

RUN uv sync --locked --no-dev

ENTRYPOINT ["uv", "run", "--no-sync", "python", "main.py"]
