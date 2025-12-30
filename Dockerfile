# Multi-stage Dockerfile for Generative GAF Trading Engine
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy workspace configuration
COPY pyproject.toml ./
COPY lms/banis/pyproject.toml ./lms/banis/
COPY lms/banis/requirements.txt ./lms/banis/

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r lms/banis/requirements.txt

# Copy application code
COPY lms/banis/ ./lms/banis/
COPY shared/ ./shared/

# Install the package in development mode
WORKDIR /app/lms/banis
RUN pip install -e .

# Set Python path to include the source directory
ENV PYTHONPATH=/app/lms/banis/src:${PYTHONPATH}

# Set working directory back to app root
WORKDIR /app

# Expose the port that the app runs on
EXPOSE 8000

# Default command - can be overridden
CMD ["python", "-m", "brainnet.services.main", "server", "--host", "0.0.0.0", "--port", "8000"]
