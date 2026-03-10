FROM python:3.11-slim
WORKDIR /app
COPY apps/auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/auth-service/ .
ENV PYTHONPATH=/app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8010/health || exit 1
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8010}"]
