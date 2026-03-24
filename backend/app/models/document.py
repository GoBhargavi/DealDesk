"""SQLAlchemy models for Document entities."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    """Document entity representing uploaded deal documents."""
    
    __tablename__ = "documents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default="Uploading",
        nullable=False
    )
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_risks: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    key_terms: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    # Foreign key
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deals.id"),
        nullable=False
    )
    
    # Relationship
    deal: Mapped["Deal"] = relationship("Deal", back_populates="documents")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, deal_id={self.deal_id})>"
