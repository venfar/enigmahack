FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /venv && \
    . /venv/bin/activate && \
    pip install -r requirements.txt

COPY . .

FROM python:3.11-slim

WORKDIR /app

RUN useradd -m appuser

COPY --from=builder /venv /venv

COPY --from=builder --chown=appuser:appuser /app /app

ENV PATH="/venv/bin:$PATH"

USER appuser

EXPOSE 8000

CMD ["python", "-m", "app.main"]