# ── AI Venture Studio OS — Dockerfile raíz ───────────────────────────────────
# Imagen base estándar para todos los servicios Python del monorepo.
# Para Railway: apunta a este Dockerfile y configura WORKDIR según el servicio.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Metadatos
LABEL org.opencontainers.image.title="AI Venture Studio OS"
LABEL org.opencontainers.image.version="1.0.0"

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY apps/backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copiar el código del backend
COPY apps/backend/ .

# Puerto por defecto (Railway asigna $PORT automáticamente)
EXPOSE 8000

# Health check para Railway / Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Comando de inicio — Railway inyecta $PORT en tiempo de ejecución
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
