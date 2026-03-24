"""Pydantic schemas package."""

from app.schemas.deal import Deal, DealCreate, DealUpdate, DealStageUpdate, DealList
from app.schemas.contact import Contact, ContactCreate, ContactUpdate, ContactList
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentList,
    DocumentUploadResponse,
    DocumentAnalysisResult
)

__all__ = [
    "Deal",
    "DealCreate",
    "DealUpdate",
    "DealStageUpdate",
    "DealList",
    "Contact",
    "ContactCreate",
    "ContactUpdate",
    "ContactList",
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentList",
    "DocumentUploadResponse",
    "DocumentAnalysisResult"
]
