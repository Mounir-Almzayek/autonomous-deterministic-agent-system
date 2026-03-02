# ADAS API – multi-stage, non-root, minimal runtime
# Build with: DOCKER_BUILDKIT=1 docker build -t adas-api .
FROM python:3.12-slim as builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-docker.txt .
# Cache mount for pip (faster rebuilds when only code changes)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements-docker.txt

# -----------------------------------------------------------------------------
# Runtime stage: only app + venv, no build tools
# -----------------------------------------------------------------------------
FROM python:3.12-slim as api

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Non-root user for security
RUN groupadd --gid 1000 adas && useradd --uid 1000 --gid adas --shell /bin/false --create-home adas

WORKDIR /app

# Copy venv from builder (reuse layer cache when requirements-docker.txt unchanged)
COPY --from=builder /opt/venv /opt/venv

# Application code (order last for better cache reuse)
COPY app/ ./app/
COPY dashboard/ ./dashboard/

# Optional: single module at root if you run with python -m
# COPY *.py ./

RUN chown -R adas:adas /app
USER adas

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)" || exit 1

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
