"""
SAMVAD AI — Step 7: RAG + Vector Search Knowledge Layer
Provides semantic retrieval of support and procedural resources based on natural human complaints.

OPERATIONAL BOUNDARIES:
- Decision-support signals for human operators only.
- Does NOT determine SVI risk levels (LOW, MODERATE, HIGH, CRITICAL).
- Does NOT override or downgrade safety flags (human_review remains True).
- Zero hallucination: only retrieves curated documents from the local knowledge base.
"""

import json
import logging
import math
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("samvad.rag")

BASE_DIR = Path(__file__).resolve().parent
_env_knowledge = os.environ.get("RAG_KNOWLEDGE_FILE")
KNOWLEDGE_FILE = Path(_env_knowledge) if _env_knowledge else (BASE_DIR / "knowledge" / "documents.json")
_env_cache = os.environ.get("RAG_VECTOR_CACHE")
CACHE_FILE = Path(_env_cache) if _env_cache else (BASE_DIR / "knowledge" / "vector_cache.pt")

# Minimum cosine similarity threshold to avoid hallucination / irrelevant retrieval
DEFAULT_MIN_SIMILARITY = 0.28


class RAGService:
    """
    Semantic Vector Search and Retrieval-Augmented Generation (RAG) Service.
    Indexes curated knowledge items and retrieves top-k relevant documents.
    """

    def __init__(self, knowledge_file: Optional[Path] = None):
        self.knowledge_file = knowledge_file or KNOWLEDGE_FILE
        self.documents: List[Dict[str, Any]] = []
        self._doc_embeddings = None
        self._is_initialized = False

    def load_documents(self) -> List[Dict[str, Any]]:
        """Load and validate knowledge documents from disk."""
        if not self.knowledge_file.exists():
            logger.warning("Knowledge file not found at %s", self.knowledge_file)
            return []
        try:
            with open(self.knowledge_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.documents = data
                return self.documents
        except Exception as exc:
            logger.error("Error loading knowledge documents: %s", exc)
        return []

    def _ensure_embeddings(self) -> bool:
        """Compute or load vector embeddings for all documents."""
        if self._is_initialized and self._doc_embeddings is not None:
            return True

        if not self.documents:
            self.load_documents()
        if not self.documents:
            return False

        try:
            import torch
            import torch.nn.functional as F

            try:
                from .indicbert_service import indicbert_service
            except ImportError:
                from indicbert_service import indicbert_service

            # Try loading cache if valid
            if CACHE_FILE.exists():
                try:
                    cache_data = torch.load(CACHE_FILE, weights_only=False)
                    if (
                        isinstance(cache_data, dict)
                        and "embeddings" in cache_data
                        and len(cache_data.get("ids", [])) == len(self.documents)
                    ):
                        self._doc_embeddings = cache_data["embeddings"]
                        self._is_initialized = True
                        logger.info("Loaded %d document embeddings from cache.", len(self.documents))
                        return True
                except Exception as c_err:
                    logger.debug("Cache reload skipped: %s", c_err)

            # Compute embeddings using IndicBERT or lightweight semantic fallback
            tensors = []
            doc_ids = []
            for doc in self.documents:
                text_to_embed = f"{doc.get('title', '')}. {doc.get('content', '')}"
                t = None
                try:
                    t = indicbert_service.get_embedding_tensor(text_to_embed)
                except Exception:
                    t = None

                if t is not None:
                    # Normalize vector
                    t_norm = F.normalize(t.unsqueeze(0), p=2, dim=1)[0]
                    tensors.append(t_norm)
                else:
                    # Fast fallback semantic vector based on character and n-gram hash
                    fb = self._compute_fallback_vector(text_to_embed)
                    tensors.append(fb)
                doc_ids.append(doc.get("id"))

            if tensors:
                self._doc_embeddings = torch.stack(tensors)
                try:
                    torch.save({"embeddings": self._doc_embeddings, "ids": doc_ids}, CACHE_FILE)
                except Exception:
                    pass
                self._is_initialized = True
                logger.info("Computed and cached %d document embeddings.", len(tensors))
                return True

        except Exception as exc:
            logger.error("Failed to compute embeddings: %s", exc)

        return False

    def _compute_fallback_vector(self, text: str):
        """Fallback normalized 768-dim pseudo-semantic hash embedding if IndicBERT model is unavailable."""
        import torch
        import torch.nn.functional as F

        vec = torch.zeros(768, dtype=torch.float32)
        words = re.findall(r"\w+", text.lower())
        for idx, word in enumerate(words):
            h = hash(word) % 768
            vec[h] += 1.0 / (idx + 1.0)
        norm = torch.norm(vec, p=2)
        if norm > 1e-6:
            vec = vec / norm
        return vec

    def _get_query_vector(self, query: str):
        """Compute normalized 768-dim vector for user query."""
        import torch
        import torch.nn.functional as F

        try:
            from .indicbert_service import indicbert_service
        except ImportError:
            from indicbert_service import indicbert_service

        t = None
        try:
            t = indicbert_service.get_embedding_tensor(query)
        except Exception:
            t = None

        if t is not None:
            return F.normalize(t.unsqueeze(0), p=2, dim=1)[0]
        return self._compute_fallback_vector(query)

    def retrieve(
        self,
        query: str,
        language: str = "english",
        top_k: int = 3,
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
    ) -> Dict[str, Any]:
        """
        Retrieve top-k relevant knowledge resources for a given natural complaint query.
        Guarantees zero hallucination by enforcing a minimum relevance score.
        """
        cleaned_query = (query or "").strip()
        if not cleaned_query:
            return {
                "status": "invalid_query",
                "query": query,
                "language": language,
                "count": 0,
                "results": [],
                "message": "Query must not be empty.",
            }

        self._ensure_embeddings()
        if not self.documents or self._doc_embeddings is None:
            return {
                "status": "knowledge_base_unavailable",
                "query": cleaned_query,
                "language": language,
                "count": 0,
                "results": [],
                "message": "Knowledge base vector index is currently unavailable.",
            }

        import torch
        import torch.nn.functional as F

        query_vec = self._get_query_vector(cleaned_query)

        # Compute cosine similarities
        similarities = F.cosine_similarity(self._doc_embeddings, query_vec.unsqueeze(0), dim=1)
        sim_scores = similarities.cpu().tolist()

        norm_q = cleaned_query.lower()
        domain_cues = [
            "complaint", "status", "process", "proceed", "document", "file", "inquiry", "next steps",
            "support", "help", "talk", "listen", "counsel", "stress", "pressure", "overwhelmed",
            "crisis", "struggling", "alone", "legal", "lawyer", "court", "rights", "safe", "safety",
            "danger", "threat", "protect", "delay", "officer", "resolution", "action",
            "तक्रार", "मदत", "कागदपत्रे", "स्थिती", "ताण", "भीती", "काळजी", "धोका",
            "शिकायत", "मदद", "प्रक्रिया", "स्थिति", "दस्तावेज", "तनाव", "खतरा", "सुरक्षा",
            "jaankari", "samajh", "tension", "pahije", "chahiye"
        ]
        has_domain_cue = any(cue in norm_q for cue in domain_cues)
        max_sim = max(sim_scores) if sim_scores else 0.0

        # Zero-hallucination out-of-domain filter:
        # If query has no citizen intake/support cues and weak semantic alignment, reject as irrelevant
        if not has_domain_cue and max_sim < 0.68:
            return {
                "status": "no_relevant_resource_found",
                "query": cleaned_query,
                "language": language,
                "count": 0,
                "results": [],
                "disclaimer": (
                    "No verified knowledge resource exceeded the minimum relevance threshold. "
                    "SAMVAD AI strictly avoids generating ungrounded facts or fabricated advice."
                ),
            }

        scored_docs = []
        for idx, score in enumerate(sim_scores):
            clamped_score = max(0.0, min(1.0, float(score)))
            doc = self.documents[idx]

            # Domain keyword boosting (e.g. process keywords, counseling keywords, safety keywords)
            norm_q = cleaned_query.lower()
            bonus = 0.0
            cat = doc.get("category", "")
            if cat == "complaint_process" and any(w in norm_q for w in ["process", "proceed", "status", "document", "कागदपत्रे", "प्रक्रिया", "स्थिति"]):
                bonus += 0.12
            elif cat in ("support_pathways", "counselling_resources") and any(w in norm_q for w in ["talk", "support", "pressure", "stress", "बोलायचे", "मदत", "तनाव"]):
                bonus += 0.12
            elif cat == "legal_aid_information" and any(w in norm_q for w in ["legal", "lawyer", "कानूनी", "वकील", "कायदा"]):
                bonus += 0.14
            elif cat == "safety_crisis_protocol" and any(w in norm_q for w in ["safe", "danger", "threat", "सुरक्षित", "धोका", "खतरा"]):
                bonus += 0.15

            final_score = round(min(1.0, clamped_score + bonus), 4)

            if final_score >= min_similarity:
                scored_docs.append({
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "category": doc.get("category"),
                    "content": doc.get("content"),
                    "language": doc.get("language", "en"),
                    "source": doc.get("source"),
                    "source_type": doc.get("source_type", "prototype_demo"),
                    "relevance_score": final_score,
                })

        # Rank by relevance score descending
        scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_results = scored_docs[:top_k]

        if not top_results:
            return {
                "status": "no_relevant_resource_found",
                "query": cleaned_query,
                "language": language,
                "count": 0,
                "results": [],
                "disclaimer": (
                    "No verified knowledge resource exceeded the minimum relevance threshold. "
                    "SAMVAD AI strictly avoids generating ungrounded facts or fabricated advice."
                ),
            }

        return {
            "status": "success",
            "query": cleaned_query,
            "language": language,
            "count": len(top_results),
            "results": top_results,
            "disclaimer": (
                "Prototype knowledge retrieval for decision support only. "
                "Not autonomous legal, medical, or emergency advice. Human operator review required."
            ),
        }


# Singleton service instance
rag_service = RAGService()
