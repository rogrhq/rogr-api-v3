# Multi-stage build for slim runtime
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app

# Default runtime env (override at deploy)
ENV PORT=8000
EXPOSE 8000

# Use single worker by default; override with APP_WORKERS for Postgres deployments
ENV APP_WORKERS=1

CMD ["bash", "-lc", "bash scripts/run_prod.sh"]