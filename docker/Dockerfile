FROM python:3.11-slim
LABEL maintainer="Abimbola Ronald"
LABEL email="abimbolaaderinsola212@gmail.com"

ENV PYTHONUNBUFFERED=1

# Create directories
RUN mkdir -p /app && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static

WORKDIR /app

# Install system dependencies including curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    libjpeg-dev \
    libpq-dev \
    gcc \
    python3-dev \
    zlib1g-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /pyenv && \
    /pyenv/bin/pip install --upgrade pip setuptools wheel

# Copy requirements files
COPY requirements.txt /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt

# Install Python dependencies
ARG DEV=false
RUN /pyenv/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
    /pyenv/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -f /tmp/requirements.txt /tmp/requirements.dev.txt

# Create non-root user
RUN adduser \
    --disabled-password \
    --gecos "" \
    --no-create-home \
    django-user && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chown -R django-user:django-user /app

# Set PATH to include virtual environment
ENV PATH="/pyenv/bin:$PATH"

# Switch to non-root user
USER django-user

# Copy application code (this should be done last or via volume mount)
COPY --chown=django-user:django-user app/ /app/

# Copy environment file if it exists
COPY --chown=django-user:django-user .env /app/.env

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "app.wsgi:application"]
