# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /app
RUN pip install --upgrade pip
COPY pyproject.toml README.md /app/
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN adduser --disabled-password --gecos '' appuser && mkdir -p /app && chown -R appuser /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*
COPY src /app/src
COPY .env /app/.env
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
