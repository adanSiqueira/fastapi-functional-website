# BUILD STAGE
FROM python:3.14.4-slim-bookworm AS builder

WORKDIR /app

# Install system dependencies (optional but common)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# PRODUCTION STAGE
FROM python:3.14.4-slim-bookworm

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Set PATH
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Security: non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run app
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'"]