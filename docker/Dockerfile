FROM python:3.11-slim
LABEL maintainer="Abimbola Ronald"
LABEL email="abimbolaaderinsola212@gmail.com"

ENV PYTHONUNBUFFERED 1

# Create directories first
RUN mkdir -p /app && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    libjpeg-dev \
    libpq-dev \
    gcc \
    python3-dev \
    zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /pyenv && \
    /pyenv/bin/pip install --upgrade pip setuptools wheel

# Copy requirements
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

# Install Python dependencies
ARG DEV=false
RUN /pyenv/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
    /pyenv/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -f /tmp/requirements.txt /tmp/requirements.dev.txt

# Create non-root user (Debian-compatible syntax)
RUN adduser \
    --disabled-password \
    --gecos "" \
    --no-create-home \
    django-user && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol

# Copy application code
COPY ./app /app

EXPOSE 8000
ENV PATH="/pyenv/bin:$PATH"
USER django-user
