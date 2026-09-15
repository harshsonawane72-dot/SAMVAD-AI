from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Integer, String, Text

try:
    from .database import Base
except ImportError:
    from database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    statement = Column(Text, nullable=False)
    language = Column(String(32), default="english", nullable=False)
    interaction_type = Column(String(32), default="chat", nullable=False)
    consent = Column(Boolean, default=True, nullable=False)
    status = Column(String(32), default="received", nullable=False)
    created_at = Column(
        String(64),
        default=lambda: datetime.now(timezone.utc).isoformat(),
        nullable=False,
    )
    # Optional assessment fields
    risk_level = Column(String(32), nullable=True)
    svi_score = Column(Integer, nullable=True)
    human_review = Column(Boolean, nullable=True)
    indicators = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "statement": self.statement,
            "language": self.language,
            "interaction_type": self.interaction_type,
            "consent": self.consent,
            "status": self.status,
            "created_at": self.created_at,
            "risk_level": self.risk_level,
            "svi_score": self.svi_score,
            "human_review": self.human_review,
            "indicators": self.indicators,
        }
