"""Document service for file operations and processing."""

import os
import uuid
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.redis_service import publish_event


class DocumentService:
    """Service class for document operations."""
    
    @staticmethod
    async def get_documents_by_deal(
        db: AsyncSession,
        deal_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """
        Get all documents for a deal.
        
        Args:
            db: Database session
            deal_id: Deal UUID
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of Document objects
        """
        result = await db.execute(
            select(Document)
            .where(Document.deal_id == deal_id)
            .offset(skip)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_document_by_id(db: AsyncSession, document_id: UUID) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            db: Database session
            document_id: Document UUID
            
        Returns:
            Document object or None if not found
        """
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_document(
        db: AsyncSession,
        deal_id: UUID,
        filename: str,
        file_type: str,
        s3_key: str
    ) -> Document:
        """
        Create a new document record.
        
        Args:
            db: Database session
            deal_id: Deal UUID
            filename: Original filename
            file_type: Document type (CIM, NDA, etc.)
            s3_key: S3 storage key
            
        Returns:
            Created Document object
        """
        document = Document(
            deal_id=deal_id,
            filename=filename,
            file_type=file_type,
            s3_key=s3_key,
            status="Processing"
        )
        db.add(document)
        await db.flush()
        await db.refresh(document)
        
        return document
    
    @staticmethod
    async def update_document(
        db: AsyncSession,
        document_id: UUID,
        document_data: DocumentUpdate
    ) -> Optional[Document]:
        """
        Update a document.
        
        Args:
            db: Database session
            document_id: Document UUID
            document_data: Update data
            
        Returns:
            Updated Document or None if not found
        """
        document = await DocumentService.get_document_by_id(db, document_id)
        if not document:
            return None
        
        update_data = document_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)
        
        await db.flush()
        await db.refresh(document)
        
        # If status changed to Ready, publish event
        if update_data.get("status") == "Ready":
            await publish_event("dealdesk:events", {
                "event": "document_ready",
                "document_id": str(document_id),
                "deal_id": str(document.deal_id)
            })
        
        return document
    
    @staticmethod
    async def delete_document(db: AsyncSession, document_id: UUID) -> bool:
        """
        Delete a document.
        
        Args:
            db: Database session
            document_id: Document UUID
            
        Returns:
            True if deleted, False if not found
        """
        document = await DocumentService.get_document_by_id(db, document_id)
        if not document:
            return False
        
        await db.delete(document)
        await db.flush()
        
        return True
    
    @staticmethod
    def generate_s3_key(filename: str, deal_id: UUID) -> str:
        """
        Generate a unique S3 key for a file.
        
        Args:
            filename: Original filename
            deal_id: Deal UUID
            
        Returns:
            S3 key string
        """
        file_extension = os.path.splitext(filename)[1]
        unique_id = str(uuid.uuid4())
        return f"deals/{deal_id}/documents/{unique_id}{file_extension}"
    
    @staticmethod
    async def update_document_status(
        db: AsyncSession,
        document_id: UUID,
        status: str,
        extracted_text: Optional[str] = None,
        summary: Optional[str] = None,
        key_risks: Optional[List[str]] = None,
        key_terms: Optional[dict] = None
    ) -> Optional[Document]:
        """
        Update document processing status and analysis results.
        
        Args:
            db: Database session
            document_id: Document UUID
            status: New status
            extracted_text: Extracted text content
            summary: Document summary
            key_risks: List of identified risks
            key_terms: Extracted key terms
            
        Returns:
            Updated Document or None if not found
        """
        document = await DocumentService.get_document_by_id(db, document_id)
        if not document:
            return None
        
        document.status = status
        if extracted_text is not None:
            document.extracted_text = extracted_text
        if summary is not None:
            document.summary = summary
        if key_risks is not None:
            document.key_risks = key_risks
        if key_terms is not None:
            document.key_terms = key_terms
        
        await db.flush()
        await db.refresh(document)
        
        # Publish event if ready
        if status == "Ready":
            await publish_event("dealdesk:events", {
                "event": "document_ready",
                "document_id": str(document_id),
                "deal_id": str(document.deal_id)
            })
        
        return document
