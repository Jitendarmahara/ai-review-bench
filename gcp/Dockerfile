# Build from the repo root: docker build -f gcp/Dockerfile -t <image> .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

COPY reports.py ./
COPY migrations/ ./migrations/
COPY gcp/main.py ./main.py

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080
CMD ["python3", "main.py"]
