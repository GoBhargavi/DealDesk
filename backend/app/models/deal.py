"""SQLAlchemy models for Deal entities."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Float, Date, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Deal(Base):
    """M&A deal entity representing a transaction in the pipeline."""
    
    __tablename__ = "deals"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_company: Mapped[str] = mapped_column(String(255), nullable=False)
    acquirer_company: Mapped[str] = mapped_column(String(255), nullable=False)
    deal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="Origination")
    deal_value_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_close_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    lead_banker: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_team: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact",
        back_populates="deal",
        cascade="all, delete-orphan"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="deal",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, name={self.name}, stage={self.stage})>"
