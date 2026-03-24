"""Pydantic schemas for Document entities."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    """Base document schema with common fields."""
    filename: str
    file_type: str
    s3_key: str
    status: str = "Uploading"
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    key_risks: List[str] = []
    key_terms: Dict[str, Any] = {}


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    deal_id: UUID


class DocumentUpdate(BaseModel):
    """Schema for updating document fields."""
    status: Optional[str] = None
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    key_risks: Optional[List[str]] = None
    key_terms: Optional[Dict[str, Any]] = None


class DocumentInDBBase(DocumentBase):
    """Base schema for documents stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    deal_id: UUID
    created_at: datetime


class Document(DocumentInDBBase):
    """Complete document schema returned from API."""
    pass


class DocumentList(BaseModel):
    """Schema for list of documents."""
    documents: List[Document]
    total: int


class DocumentUploadResponse(BaseModel):
    """Response schema after document upload."""
    document: Document
    message: str


class DocumentAnalysisRequest(BaseModel):
    """Request schema for document analysis."""
    document_id: UUID


class DocumentAnalysisResult(BaseModel):
    """Result schema for document analysis."""
    document_id: UUID
    summary: str
    key_risks: List[Dict[str, Any]]
    key_terms: Dict[str, Any]
    document_type_detected: str
