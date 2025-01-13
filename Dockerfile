FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /uvx /bin/
RUN apt-get update && \
    apt-get install -y \
    curl \
    ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/bin

WORKDIR /app

COPY ./Justfile ./Justfile
COPY ./pyproject.toml ./pyproject.toml
RUN just install

COPY ./strictql_postgres ./strictql_postgres
COPY ./tests ./tests


RUN just test


