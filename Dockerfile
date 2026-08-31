FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/caseflow/.local/bin:$PATH"

RUN useradd --create-home --uid 10001 caseflow
COPY --from=builder /install /usr/local
WORKDIR /app
COPY alembic.ini ./
COPY migrations ./migrations
USER caseflow
EXPOSE 8000
CMD ["uvicorn", "caseflow.api:app", "--host", "0.0.0.0", "--port", "8000"]
