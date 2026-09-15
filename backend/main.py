from datetime import datetime, timezone
from typing import Optional
import os
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from .database import Base, engine, get_db, ensure_schema_columns
    from .models import Case
    from .svi_engine import analyze_statement
    from .indicbert_service import indicbert_service
    from .bhashini_service import bhashini_service
    from .language_detection import detect_language
    from .assessment_pipeline import assess_complaint
    from .risk_classifier import risk_classifier_service
    from .rag_service import rag_service
except ImportError:
    from database import Base, engine, get_db, ensure_schema_columns
    from models import Case
    from svi_engine import analyze_statement
    from indicbert_service import indicbert_service
    from bhashini_service import bhashini_service
    from language_detection import detect_language
    from assessment_pipeline import assess_complaint
    from risk_classifier import risk_classifier_service
    from rag_service import rag_service

# Create tables in SQLite automatically on startup and ensure schema columns
Base.metadata.create_all(bind=engine)
ensure_schema_columns()

app = FastAPI(
    title="SAMVAD AI Backend",
    description="Backend API for SAMVAD AI with SQLite persistence and End-to-End AI Pipeline",
    version="1.0.0",
)

# CORS configuration: Explicitly allow the deployed Vercel frontend and local development origins
DEFAULT_ALLOWED_ORIGINS = [
    "https://samvad-ai-jet.vercel.app",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

allowed_origins_env = os.environ.get("ALLOWED_ORIGINS")
if allowed_origins_env and allowed_origins_env.strip():
    origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
else:
    origins = DEFAULT_ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CaseCreate(BaseModel):
    statement: Optional[str] = None
    language: Optional[str] = "english"
    interaction_type: Optional[str] = None
    interactionType: Optional[str] = None
    consent: Optional[bool] = None
    case_id: Optional[str] = None
    risk_level: Optional[str] = None
    svi_score: Optional[int] = None
    human_review: Optional[bool] = None
    indicators: Optional[str] = None


class AnalyzeRequest(BaseModel):
    statement: Optional[str] = None
    language: Optional[str] = "english"


class UnderstandRequest(BaseModel):
    text: Optional[str] = None
    language: Optional[str] = "Hindi"


class DetectLanguageRequest(BaseModel):
    text: Optional[str] = None


class AssessRequest(BaseModel):
    text: Optional[str] = None
    statement: Optional[str] = None
    language: Optional[str] = None
    case_id: Optional[str] = None
    interaction_type: Optional[str] = "chat"
    consent: Optional[bool] = True


class ClassifyRiskRequest(BaseModel):
    text: Optional[str] = None
    statement: Optional[str] = None
    language: Optional[str] = "english"


class RetrieveSupportRequest(BaseModel):
    text: Optional[str] = None
    query: Optional[str] = None
    language: Optional[str] = "english"
    top_k: Optional[int] = 3


@app.get("/", response_class=PlainTextResponse)
def read_root():
    return "SAMVAD AI Backend is running"


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SAMVAD AI Backend",
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    if req.statement is None or not req.statement.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statement must not be empty.",
        )
    try:
        return analyze_statement(req.statement, req.language or "english")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.post("/ai/assess")
def assess_endpoint(req: AssessRequest, db: Session = Depends(get_db)):
    """
    Unified end-to-end AI assessment endpoint (Step 8).
    Coordinates Language Detection, Risk Classification, Context-Aware SVI,
    Safety Verification, RAG Support Retrieval, and Database Persistence.
    """
    input_text = (req.text or req.statement or "").strip()
    if not input_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint text must not be empty.",
        )
    try:
        return assess_complaint(
            text=input_text,
            language=req.language,
            case_id=req.case_id,
            interaction_type=req.interaction_type or "chat",
            consent=req.consent if req.consent is not None else True,
            save_to_db=True,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment pipeline error: {str(e)}",
        )


@app.post("/ai/classify-risk")
def classify_risk_endpoint(req: ClassifyRiskRequest):
    """
    Neural natural complaint risk classification endpoint.
    """
    input_text = (req.text or req.statement or "").strip()
    if not input_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty.",
        )
    try:
        return risk_classifier_service.classify(input_text, req.language or "english")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification error: {str(e)}",
        )


@app.post("/ai/retrieve-support")
def retrieve_support_endpoint(req: RetrieveSupportRequest):
    """
    RAG semantic vector search for grounded support and procedural resources.
    """
    input_text = (req.text or req.query or "").strip()
    if not input_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must not be empty.",
        )
    try:
        return rag_service.retrieve(
            query=input_text,
            language=req.language or "english",
            top_k=req.top_k or 3,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {str(e)}",
        )


@app.post("/ai/understand")
def understand(req: UnderstandRequest):
    if req.text is None or not req.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty.",
        )
    try:
        return indicbert_service.understand(req.text, req.language or "Hindi")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}",
        )


@app.get("/ai/transcribe")
def transcribe_status():
    """
    Returns public Bhashini transcription configuration status without exposing credentials.
    """
    return bhashini_service.get_status_info()


@app.post("/ai/transcribe")
async def transcribe(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form(None, description="Language selection: en, hi, mr"),
    lang: Optional[str] = None,
):
    """
    Transcribes audio using Digital India BHASHINI ASR.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file must be provided.",
        )

    try:
        audio_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read audio file: {str(e)}",
        )

    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file must not be empty.",
        )

    selected_lang = language or lang or "hi"
    try:
        norm_lang = bhashini_service.normalize_language(selected_lang)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    try:
        bhashini_service.validate_audio(
            filename=file.filename,
            content_type=file.content_type,
            audio_bytes=audio_bytes,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not bhashini_service.is_configured():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_configured",
                "provider": "Bhashini",
                "message": "Bhashini credentials are not configured.",
                "supported_languages": ["en", "hi", "mr"],
                "disclaimer": bhashini_service.DISCLAIMER,
            },
        )

    result = bhashini_service.transcribe(
        audio_bytes=audio_bytes,
        language=norm_lang,
        filename=file.filename,
        content_type=file.content_type,
    )

    if result.get("status") == "error":
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=result,
        )

    return result


@app.post("/ai/detect-language")
def detect_language_endpoint(req: DetectLanguageRequest):
    """
    Multilingual language detection endpoint.
    """
    return detect_language(req.text)


@app.post("/cases")
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    if case_in.statement is None or not case_in.statement.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statement must not be empty.",
        )

    if case_in.consent is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent must be true.",
        )

    case_id = case_in.case_id or f"CASE-{uuid.uuid4().hex[:8].upper()}"
    interaction_type = (
        case_in.interaction_type or case_in.interactionType or "chat"
    )
    language = case_in.language or "english"
    existing = db.query(Case).filter(Case.case_id == case_id).first()
    if existing:
        existing.statement = case_in.statement.strip()
        existing.language = str(language)
        existing.interaction_type = str(interaction_type)
        existing.consent = True
        existing.status = "received"
        if case_in.risk_level is not None:
            existing.risk_level = case_in.risk_level
        if case_in.svi_score is not None:
            existing.svi_score = case_in.svi_score
        if case_in.human_review is not None:
            existing.human_review = case_in.human_review
        if case_in.indicators is not None:
            existing.indicators = case_in.indicators
        db.commit()
        db.refresh(existing)
        return existing.to_dict()

    created_at = datetime.now(timezone.utc).isoformat()
    db_case = Case(
        case_id=case_id,
        statement=case_in.statement.strip(),
        language=str(language),
        interaction_type=str(interaction_type),
        consent=True,
        status="received",
        created_at=created_at,
        risk_level=case_in.risk_level,
        svi_score=case_in.svi_score,
        human_review=case_in.human_review,
        indicators=case_in.indicators,
    )

    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    return db_case.to_dict()


@app.get("/cases")
def get_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.id.asc()).all()
    return [c.to_dict() for c in cases]


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("ENVIRONMENT", "development").lower() != "production"

    uvicorn.run("main:app", host=host, port=port, reload=reload)
