# SAMVAD AI — Step 12A: Practical Deployment Architecture & Implementation Plan

**Target Event**: Smart India Hackathon (SIH) Prototype Demonstration  
**Frontend Hosting Target**: Vercel (Static HTML / CSS / JavaScript)  
**Backend Hosting Target**: Hugging Face Spaces (Docker/FastAPI) or Railway  
**Fallback Demo Host**: Cloudflare Tunnel to Local Machine  

---

## 1. Comparative Analysis of Backend Hosting Options

| Hosting Platform | RAM Allocation | CPU | Persistent Storage | Free / Low-Cost Availability | Cold-Start Behavior | IndicBERT & Model Suitability | SIH Demo Readiness & Risk |
|---|---|---|---|---|---|---|---|
| **Hugging Face Spaces (Docker/FastAPI)** | **16 GB RAM** (Free standard CPU) | 2 vCPUs | Ephemeral (50 GB) + optional persistent storage | **100% Free** on CPU Basic tier | Sleeps after 48h inactivity; wake-up takes ~30–45s | ⭐⭐⭐⭐⭐ **Exceptional**: 16 GB RAM provides massive headroom for PyTorch + IndicBERT without OOM | **Recommended Primary Option**: Free, stable public HTTPS URL, zero risk of memory exhaustion. |
| **Railway** | Up to **8 GB RAM** (configurable) | Shared / Dedicated | Persistent Volumes supported ($0.25/GB) | $5/month trial credits; ~$5–$10/mo ongoing | No cold-start; runs continuously | ⭐⭐⭐⭐ **High**: Can scale machine memory to 4 GB–8 GB | **Recommended Paid Option**: Highly reliable, native GitHub deploy, custom domain support. |
| **Render** | 512 MB (Free) / 2 GB ($25/mo) / 4 GB ($85/mo) | Shared / 1–2 vCPUs | Disks on paid tiers only ($0.25/GB) | Free tier exists, but capped at 512 MB | 50s spin-up after 15 min idle | ❌ **Unusable on Free Tier**: 512 MB triggers instant Out-Of-Memory (OOM) crash on PyTorch load. | Risky unless paying $25–$85/month for upgraded RAM. |
| **Fly.io** | Configurable (256 MB to 8 GB+) | 1–4 vCPUs | Persistent Volumes | Pay-as-you-go (~$10–$15/mo for 4 GB RAM) | Fast machine auto-start/stop | ⭐⭐⭐⭐ **Good**: Dedicated memory control | Requires credit card setup and CLI-driven configuration. |
| **Cloudflare Tunnel (Local Machine)** | Host machine RAM (e.g. 16 GB+) | Host machine CPU/GPU | Local SSD (SQLite `samvad.db`) | **100% Free** | **0s Cold-Start** (instant response) | ⭐⭐⭐⭐⭐ **Instant**: Model is already loaded in memory locally | **Emergency Fallback**: Rock-solid live backup during hackathon judging; immune to cloud build failures. |

---

## 2. Recommended Hosting Strategy

### Primary Recommendation: **Hugging Face Spaces (FastAPI + Docker)**
- **Why**:
  1. **Memory Guarantee**: Provides **16 GB of RAM for free** on standard CPU instances. IndicBERT requires ~2.5–3.5 GB active RAM under load. Render and other free tiers with 512 MB will crash immediately; HF Spaces handles this effortlessly.
  2. **Native PyTorch & Transformers Support**: Hosted directly on Hugging Face infrastructure, providing ultra-fast model weight pulls for `ai4bharat/IndicBERTv2-MLM-only`.
  3. **Instant Public HTTPS**: Exposes an automatic SSL-secured endpoint (`https://<username>-samvad-ai-backend.hf.space`) ready to connect to Vercel.
  4. **Simple Git / Docker Integration**: Deployable by pushing a `Dockerfile` and repository files.

### Emergency Stage Backup: **Cloudflare Tunnel (`cloudflared`)**
- If cloud networking or internet access is throttled at the hackathon venue, running `cloudflared tunnel --url http://127.0.0.1:8000` gives an instant public HTTPS URL pointing to the local machine, eliminating cloud latency and cold-starts completely.

---

## 3. Database Strategy

### Mode 1: Local Prototyping & Development
- **Engine**: SQLite (`backend/samvad.db`).
- **Configuration**: `DATABASE_URL=sqlite:///backend/samvad.db`.
- **Characteristics**: Fast, zero setup, self-contained.

### Mode 2: Public SIH Hackathon Demo
- **Engine**: **Single-Instance SQLite** OR **Free Managed PostgreSQL (Neon / Supabase)**.
- **Tradeoff Analysis**:
  - *Option A (Recommended for SIH Demo — Single-Instance SQLite)*:
    Because the SIH presentation is a controlled demonstration with 1–5 concurrent requests from the jury and team, running a single-worker container on HF Spaces or Railway with SQLite is **extremely stable**. It avoids external database connection drops, SSL timeouts, or network hops.
  - *Option B (PostgreSQL via Neon/Supabase)*:
    If multi-instance horizontal scaling is desired, set `DATABASE_URL=postgresql+psycopg2://user:password@ep-xyz.neon.tech/samvad` in environment variables. `backend/database.py` already automatically detects and connects to PostgreSQL when this variable is populated.

---

## 4. Frontend Configuration & Dynamic API Routing

### Vercel Deployment for Frontend
- The frontend (`index.html`, `assessment.html`, `dashboard.html`) is deployed to Vercel as a static site.
- Frontend scripts dynamically determine the backend URL using `window.SAMVAD_API_BASE_URL`:
  ```javascript
  var BACKEND_API_BASE = (typeof window !== "undefined" && window.SAMVAD_API_BASE_URL)
    ? window.SAMVAD_API_BASE_URL
    : "http://127.0.0.1:8000";
  ```
- In Vercel production:
  Create a lightweight `config.js` or inject into `<head>`:
  ```html
  <script>
    window.SAMVAD_API_BASE_URL = "https://your-username-samvad-backend.hf.space";
  </script>
  ```
- In local development:
  No configuration file is needed; it defaults automatically to `http://127.0.0.1:8000`.

---

## 5. CORS Configuration

In `backend/main.py`, CORS is dynamically driven by the `ALLOWED_ORIGINS` environment variable:
```python
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins_env and allowed_origins_env.strip():
    origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
else:
    origins = ["*"]
```

### Production Setting on Backend:
```bash
ALLOWED_ORIGINS=https://samvad-ai.vercel.app,http://localhost:3000,http://127.0.0.1:8000
```
*(Prevents arbitrary third-party web pages from submitting unauthorized requests while allowing the Vercel app and local testing).*

---

## 6. Model Resource Requirements & Cold-Start Optimization

1. **IndicBERT Base**:
   - Model: `ai4bharat/IndicBERTv2-MLM-only` (~480 MB download).
   - CPU Inference Latency: ~250–450 ms per complaint (thoroughly acceptable for administrative triaging).
   - Memory Consumption: ~2.5 GB peak on model load, ~1.8 GB steady-state.
2. **Classification Head**:
   - Weights: `backend/models/risk_classifier_head.pt` (405 KB).
   - Instant loading (< 10 ms).
3. **Cold-Start Warmup**:
   - To avoid a 15-second delay when the hackathon jury tests the first complaint, configure a warmup hook in FastAPI startup (`@app.on_event("startup")` or lifespan) that runs one lightweight dummy forward pass on boot.

---

## 7. Security Architecture: SIH Prototype vs. Real Production

| Security Domain | SIH Prototype Standard (Current) | Future Real-World Production Standard |
|---|---|---|
| **Transport Layer** | HTTPS enforced via Vercel & HF Spaces / Cloudflare | Strict HSTS, TLS 1.3, Certificate Pinning |
| **Authentication** | Open access for demo evaluation; role simulation | OAuth2 / OpenID Connect, Multi-Factor Auth (MFA) for Operators |
| **CORS Policy** | Restricted to Vercel origin + local dev origins | Strict origin restriction + CSRF tokens |
| **Audio File Ingestion** | Format & extension validation; in-memory buffer limit | Antivirus scanning, dedicated S3 bucket with signed upload URLs |
| **Privacy & Logging** | No PII or raw complaints logged to console/disk | End-to-end field-level encryption, audit compliance logs |
| **Disclaimer** | AI-assisted prototype notice visible on all pages | Statutory legal disclaimer & administrative routing notices |

---

## 8. Bhashini Integration Strategy

- **Credentials Optional**: Backend boots cleanly whether Bhashini credentials are present or absent.
- **Client Fallback**: If unconfigured, `GET /ai/transcribe` returns `status: "not_configured"`, and the browser immediately activates Web Speech API (`webkitSpeechRecognition`).
- **Demo Recommendation**:
  - For the jury presentation, rely on the built-in browser Web Speech API (zero latency, zero external API failure risk).
  - If official MeitY Bhashini API credentials are provided later, inject them into HF Spaces environment variables without changing any code.

---

## 9. RAG Knowledge Layer Deployment

- Curated knowledge base ([`backend/knowledge/documents.json`](file:///d:/sih/SAMVAD%20AI/backend/knowledge/documents.json)) and precomputed embeddings ([`backend/knowledge/vector_cache.pt`](file:///d:/sih/SAMVAD%20AI/backend/knowledge/vector_cache.pt)) are committed and packaged directly inside the Docker image / repository.
- **Zero External Vector DB**: No Pinecone, Milvus, or external vector service is required. In-memory cosine similarity search executes in < 5 ms.
- **Zero Hallucination Guardrail**: Cosine similarity cutoff at `0.28` prevents hallucinated advice on out-of-domain queries.

---

## 10. Complete Deployment Architecture Diagram

```
[ Citizen Browser / Jury Device ]
               │
               ▼  HTTPS (Vercel CDN)
[ Vercel: SAMVAD AI Frontend ]
  - index.html, assessment.html, dashboard.html
  - assessment.js (points to window.SAMVAD_API_BASE_URL)
               │
               ▼  HTTPS / CORS (JSON REST)
[ Hugging Face Spaces / Railway: FastAPI Container ]
  │  (2 vCPUs, 16 GB RAM)
  │
  ├─── Language Detection (language_detection.py)
  ├─── IndicBERT Text Representation (ai4bharat/IndicBERTv2)
  ├─── Neural Risk Classifier Head (risk_classifier_head.pt)
  ├─── Contextual Safety Engine (contextual_safety.py)
  ├─── Context-Aware SVI Formula Engine (svi_engine.py)
  ├─── RAG Vector Retriever (documents.json + vector_cache.pt)
  └─── SQLite / PostgreSQL Persistence (samvad.db)
```

---

## 11. Step-by-Step Deployment Plan (Phases A through G)

### Phase A: Backend Preparation
1. Create `backend/Dockerfile` using lightweight Python 3.11/3.12 base image.
2. Install PyTorch CPU-only (`pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu`) to keep Docker image < 1.5 GB.
3. Verify that `risk_classifier_head.pt`, `vector_cache.pt`, and `documents.json` are copied into the container image.

### Phase B: Backend Deployment (Hugging Face Spaces)
1. Create a new Space on Hugging Face: Type = **Docker**, Hardware = **CPU Basic (Free, 16 GB RAM)**.
2. Push backend code and `Dockerfile` to the Space repository.
3. Configure Environment Variables in Space Settings:
   - `ENVIRONMENT=production`
   - `ALLOWED_ORIGINS=https://samvad-ai.vercel.app`
4. Verify backend health endpoint: `https://<space-name>.hf.space/health` returns `200 OK`.

### Phase C: Database Configuration
1. For single-container demo: SQLite database initializes automatically at startup.
2. Run database health check (`GET /cases`).

### Phase D: Frontend API Configuration
1. In `index.html`, `assessment.html`, and `dashboard.html`, add:
   ```html
   <script>window.SAMVAD_API_BASE_URL = "https://<your-space>.hf.space";</script>
   ```
2. Deploy frontend repository to Vercel via GitHub integration.

### Phase E: CORS Configuration
1. Update `ALLOWED_ORIGINS` in backend environment with the assigned Vercel URL (e.g. `https://samvad-ai.vercel.app`).
2. Test preflight `OPTIONS` request.

### Phase F: End-to-End Live Verification
1. Submit test complaint in English: Verify SVI score, risk tier, and RAG resource cards appear.
2. Submit test complaint in Hindi/Marathi: Verify Devanagari language detection and classification.
3. Submit critical crisis complaint: Verify safety alert and operator escalation flag appear.
4. Open `dashboard.html`: Verify case appears in real-time in the operator queue.

### Phase G: SIH Demo Day Checklist & Resilience Backup
- [ ] **T-60 Minutes**: Send one test complaint to warm up the Hugging Face container from idle sleep.
- [ ] **Microphone Permission**: Test Chrome microphone access for voice input on the presentation laptop.
- [ ] **Offline / Fallback Confirmation**: Test disconnecting internet briefly to ensure MockAI prototype fallback displays "Demo / Offline Mode" rather than crashing.
- [ ] **Emergency Hot-Standby**: Keep `python -m uvicorn backend.main:app` running locally on laptop with Cloudflare tunnel ready if venue Wi-Fi blocks external ports.
