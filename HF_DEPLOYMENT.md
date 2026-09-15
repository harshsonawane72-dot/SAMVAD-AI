# SAMVAD AI — Hugging Face Spaces Backend Deployment Guide

**Target Platform**: Hugging Face Spaces (Docker SDK)  
**Hardware Tier**: CPU Basic (2 vCPU, 16 GB RAM) — Free  
**Container Entrypoint**: `uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}`  
**Application Port**: `7860`  

---

## 1. Prerequisites Checklist

- [x] `Dockerfile` configured with `python:3.11-slim` and non-root user `user` (UID `1000`).
- [x] CPU-only PyTorch configured via `--index-url https://download.pytorch.org/whl/cpu`.
- [x] `README.md` configured with Hugging Face Spaces Docker metadata.
- [x] `.dockerignore` prevents committing `.env`, caches, and build artifacts.
- [x] Model weights (`backend/models/risk_classifier_head.pt`) present (405 KB).
- [x] RAG knowledge base (`backend/knowledge/documents.json`) and vector cache (`backend/knowledge/vector_cache.pt`) present.
- [x] Zero plaintext secrets or credentials in the repository.

---

## 2. Step-by-Step Deployment Instructions

### Step A: Create the Space on Hugging Face
1. Log in to [huggingface.co](https://huggingface.co) and navigate to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Enter Space Name: e.g. `samvad-ai-backend`.
3. Select License: `Apache 2.0` (or your preferred open source license).
4. **Select Space SDK**: Choose **Docker** (Blank).
5. **Select Space Hardware**: Choose **CPU Basic • 2 vCPU • 16 GB RAM • Free**.
6. Click **Create Space**.

---

### Step B: Deploy Repository Files

#### Option 1: Using the Hugging Face CLI (`hf` command)
From the project root directory (`d:\sih\SAMVAD AI`), run:
```bash
# 1. Login to your Hugging Face account (paste your User Access Token with write permission)
hf auth login

# 2. Upload the repository directly to your Space
hf upload <your-hf-username>/samvad-ai-backend . . --repo-type space
```

#### Option 2: Using Git
```bash
# 1. Add the Hugging Face Space as a git remote
git remote add space https://huggingface.co/spaces/<your-hf-username>/samvad-ai-backend

# 2. Push to the Space main branch
git push space main
```

#### Option 3: Direct Web UI Upload
1. In your new Space on Hugging Face, click on the **Files** tab.
2. Click **Add file** $\rightarrow$ **Upload files**.
3. Drag and drop the following files/folders from `d:\sih\SAMVAD AI`:
   - `Dockerfile`
   - `.dockerignore`
   - `README.md`
   - `backend/` (entire folder including `models/` and `knowledge/`)
4. Commit the changes. The Space will automatically trigger the Docker build.

---

### Step C: Configure Space Environment Variables
In your Hugging Face Space:
1. Navigate to **Settings** $\rightarrow$ **Variables and secrets**.
2. Under **Variables**, add:
   - `ENVIRONMENT`: `production`
   - `INDICBERT_MODEL_NAME`: `ai4bharat/IndicBERTv2-MLM-only`
   - `RISK_CLASSIFIER_WEIGHTS_PATH`: `backend/models/risk_classifier_head.pt`
   - `DATABASE_URL`: `sqlite:///backend/samvad.db`
   - `ALLOWED_ORIGINS`: If Vercel frontend URL is known, set `https://<your-app>.vercel.app,http://localhost:3000,http://127.0.0.1:8000`. If not known yet, leave empty or set to local dev origins (wildcard `*` is disallowed in production mode).
3. Under **Secrets** *(Optional — only if real keys are available)*:
   - `BHASHINI_USER_ID`: *(Optional)*
   - `BHASHINI_API_KEY`: *(Optional)*
   - `BHASHINI_INFERENCE_API_KEY`: *(Optional)*
   *(If omitted, the system safely operates with browser Web Speech API fallback).*

---

### Step D: Monitor Build and Obtain Public URL
1. Click the **App** tab to view the live Docker build logs.
2. Building takes approximately **2 to 4 minutes** (installing CPU PyTorch, transformers, and copying weights).
3. When the status changes to **Running**, your live public HTTPS endpoint is:
   ```
   https://<your-hf-username>-samvad-ai-backend.hf.space
   ```

---

## 3. Post-Deployment Verification Commands

Replace `<YOUR-SPACE-URL>` with your actual live Space URL (e.g. `https://harsh-samvad-ai-backend.hf.space`):

```bash
# 1. Health Liveness Check (Expected: HTTP 200)
curl -s https://<YOUR-SPACE-URL>/health

# 2. Test End-to-End Unified Assessment
curl -s -X POST https://<YOUR-SPACE-URL>/ai/assess \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"I want to know the status of my complaint\", \"language\": \"english\"}"

# 3. Test IndicBERT Text Understanding
curl -s -X POST https://<YOUR-SPACE-URL>/ai/understand \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"I want information about my complaint.\", \"language\": \"english\"}"

# 4. Test Neural Risk Classification
curl -s -X POST https://<YOUR-SPACE-URL>/ai/classify-risk \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"I am feeling overwhelmed with my application process.\", \"language\": \"english\"}"

# 5. Test Grounded RAG Support Retrieval
curl -s -X POST https://<YOUR-SPACE-URL>/ai/retrieve-support \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"How can I check the status of my complaint?\"}"

# 6. Test Case Management Readback
curl -s https://<YOUR-SPACE-URL>/cases

# 7. Check Bhashini Status (Expected: status: not_configured)
curl -s https://<YOUR-SPACE-URL>/ai/transcribe
```

---

## 4. Architecture & Safeguards Summary

1. **CPU Execution**: Runs purely on 2 vCPUs without GPU requirement.
2. **16 GB RAM Allocation**: Hugging Face Spaces' free tier easily accommodates IndicBERT's ~2.5 GB peak footprint.
3. **Zero Secrets Leakage**: No credentials committed or returned in JSON responses.
4. **Data Isolation**: Ephemeral SQLite database initialized at `/home/user/app/backend/samvad.db`.
5. **CORS Hardening**: Enforces strict origin matching in production (`ENVIRONMENT=production`).
