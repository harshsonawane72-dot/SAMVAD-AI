# ==============================================================================
# SAMVAD AI — Dockerfile for Hugging Face Spaces & Production Containerization
# ==============================================================================
# Base Image: Python 3.11 slim (Debian-based, lightweight Linux)
FROM python:3.11-slim

LABEL maintainer="SAMVAD AI Team"
LABEL description="SAMVAD AI Multilingual Citizen Grievance Decision-Support Backend"

# Set non-interactive environment and Python flags
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOST=0.0.0.0 \
    ENVIRONMENT=production \
    INDICBERT_MODEL_NAME=ai4bharat/IndicBERTv2-MLM-only

# Install essential system dependencies (curl for container health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-privileged user (Hugging Face Spaces requirement: UID 1000)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Install CPU-only PyTorch first to prevent installing heavy CUDA/GPU wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy backend requirements and install remaining dependencies
COPY --chown=user:user backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy all application files (including models, knowledge base, and assets)
COPY --chown=user:user . /home/user/app

# Ensure correct permissions for SQLite directory
RUN mkdir -p /home/user/app/backend && \
    chown -R user:user /home/user/app

# Switch to non-root user
USER user

# Hugging Face Spaces default port
EXPOSE 7860

# Container healthcheck testing /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-7860}/health || exit 1

# Launch FastAPI backend with Uvicorn, binding to 0.0.0.0 on the dynamically assigned PORT
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
