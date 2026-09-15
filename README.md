---
title: SAMVAD AI Backend
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# SAMVAD AI — Multilingual Citizen Grievance Decision-Support Backend

SAMVAD AI is a context-aware grievance triaging and vulnerability assessment engine developed for citizen assistance in Indian languages.

## Target Architecture

- **Frontend**: Hosted on Vercel (`index.html`, `assessment.html`, `dashboard.html`).
- **Backend**: FastAPI running inside this Hugging Face Spaces Docker container.
- **AI Core**:
  - `ai4bharat/IndicBERTv2-MLM-only` semantic text representations.
  - Multi-layer perceptron neural risk classification head (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
  - Context-aware Severity Vulnerability Index (SVI) mathematical formula.
  - Independent Contextual Safety Safeguard layer with human-review enforcement.
  - Retrieval-Augmented Generation (RAG) knowledge retrieval layer.
  - SQLite database for persistent grievance management.

## API Endpoints

- `GET /health` — Service liveness health check
- `POST /ai/assess` — Unified end-to-end grievance assessment
- `POST /ai/classify-risk` — Neural risk classification
- `POST /ai/retrieve-support` — RAG semantic knowledge retrieval
- `POST /ai/detect-language` — Multilingual language detection
- `GET /ai/transcribe` — Bhashini speech-to-text status check
- `POST /ai/transcribe` — Audio speech-to-text transcription
- `GET /cases` — Persisted case management for Human Operator Dashboard

## Prototype Notice

This application is an AI-assisted decision-support prototype. It is not a clinical diagnostic instrument or emergency dispatch system. Human review is mandatory for all high-risk grievances.
