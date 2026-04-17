FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY tests ./tests
COPY docs ./docs
COPY config.sample.yaml .
COPY .env.example .

RUN pip install --no-cache-dir -e .[dev]

ENTRYPOINT ["python", "-m", "scripts.cli"]
CMD ["fixture-run"]
