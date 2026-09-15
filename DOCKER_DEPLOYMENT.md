# SAMVAD AI — Docker Container Deployment Guide

This guide documents the containerization and execution procedures for the **SAMVAD AI FastAPI backend** targeted for **Hugging Face Spaces (Docker SDK)**.

---

## 1. Container Architecture Overview

- **Base Image**: `python:3.11-slim` (lightweight Debian-based Linux)
- **PyTorch Installation**: CPU-only via `https://download.pytorch.org/whl/cpu` (reduces image size by ~2 GB)
- **Runtime User**: Non-root UID `1000` (`user`), conforming to Hugging Face Spaces security sandbox
- **Default Application Port**: `7860` (Hugging Face default)
- **Entrypoint**: `uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}`

---

## 2. Docker Commands Reference

### A. Build the Image
```bash
docker build -t samvad-ai-backend:latest .
```
*Build flags explained:*
- `-t samvad-ai-backend:latest`: Tags the container image.
- Uses multi-stage pip caching to avoid bundling build caches.

### B. Run the Container Locally
```bash
docker run -d \
  --name samvad-backend \
  -p 7860:7860 \
  -e PORT=7860 \
  -e ENVIRONMENT=production \
  -e ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:8000" \
  samvad-ai-backend:latest
```

### C. Health & Assessment Endpoint Verification
```bash
# 1. Health Liveness Check (Expected: HTTP 200)
curl -s http://127.0.0.1:7860/health

# 2. Test Assessment Pipeline
curl -s -X POST http://127.0.0.1:7860/ai/assess \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"I want to know the status of my complaint\", \"language\": \"english\"}"

# 3. Test Cases List
curl -s http://127.0.0.1:7860/cases
```

### D. View Logs & Container Stats
```bash
# Stream live logs
docker logs -f samvad-backend

# Check CPU & RAM consumption
docker stats samvad-backend
```

### E. Stop and Clean Up Container
```bash
docker stop samvad-backend
docker rm samvad-backend
```

---

## 3. Hugging Face Spaces Deployment Steps

1. **Create Space**:
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces) $\rightarrow$ "Create new Space".
   - **Space SDK**: Select **Docker** (Blank).
   - **Hardware**: Select **CPU Basic (2 vCPU, 16 GB RAM) — FREE**.
2. **Push Code to Space Repository**:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/samvad-ai-backend
   git push space main
   ```
3. **Configure Space Secrets & Environment Variables**:
   - Navigate to Space `Settings` $\rightarrow$ `Variables and secrets`.
   - Add:
     - `ENVIRONMENT` = `production`
     - `ALLOWED_ORIGINS` = `https://<your-vercel-app>.vercel.app`
     - *(Optional)* `BHASHINI_USER_ID`, `BHASHINI_API_KEY`, `BHASHINI_INFERENCE_API_KEY`
4. **Live Verification**:
   - Open Space public URL: `https://<your-username>-samvad-ai-backend.hf.space/health`
   - Expected output: `{"status": "healthy", "service": "SAMVAD AI Backend"}`

---

## 4. Resource & Performance Profile (CPU Deployment)

| Metric | Measured / Estimated Value | Notes |
|---|---|---|
| **Docker Image Size** | ~980 MB – 1.1 GB | Optimized via CPU-only PyTorch (CUDA packages omitted) |
| **IndicBERT Peak RAM** | ~2.5 GB | Observed during initial tensor loading and tokenizer initialization |
| **IndicBERT Steady-State RAM**| ~1.8 GB | Active inference resident memory |
| **Risk Classifier Head RAM** | ~10 MB | Lightweight PyTorch MLP weights (`405 KB` disk) |
| **RAG Vector Search RAM** | < 1 MB | In-memory cosine similarity across 10 curated documents |
| **Container Cold Boot Time** | ~1.2 seconds | FastAPI + Uvicorn initialization |
| **First Inference Latency** | ~4.5 – 6.0 seconds | Initial model weights download/deserialization into memory |
| **Warm Inference Latency** | ~220 – 380 ms | Per complaint on 2 standard CPU cores |

---

## 5. Security & Isolation Safeguards

1. **Non-Root Execution**: Runs under UID `1000` (`user`), preventing container breakout or host root access.
2. **CORS Enforcement**: When `ENVIRONMENT=production`, wildcard `"*"` is strictly disabled. Only origins explicitly listed in `ALLOWED_ORIGINS` are accepted.
3. **No Hardcoded Secrets**: Secrets are injected via environment variables at runtime. `.dockerignore` prevents accidental inclusion of local `.env` files.
4. **Data Isolation**: SQLite database lives in `/home/user/app/backend/samvad.db` inside the container boundary.
