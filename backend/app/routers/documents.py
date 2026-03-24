"""Documents router for file upload and analysis."""

import json
import asyncio
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document
from app.schemas.document import Document as DocumentSchema, DocumentList, DocumentUploadResponse, DocumentAnalysisResult
from app.services.deal_service import DealService
from app.services.document_service import DocumentService
from app.services.redis_service import publish_event
from app.agents.document_agent import DocumentAgent

router = APIRouter(prefix="/documents", tags=["documents"])


def _extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF content (mock implementation)."""
    # In a real implementation, use PyPDF2 or similar
    # For now, return mock extracted text based on filename patterns
    return "Mock extracted text from PDF document. This would contain the actual document content after OCR processing."


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    deal_id: str = Form(..., description="Deal ID to associate with document"),
    file_type: str = Form(..., description="Document type (CIM, NDA, Financial, Other)"),
    db: AsyncSession = Depends(get_db)
) -> DocumentUploadResponse:
    """
    Upload a document to the deal data room.
    
    The file is saved (mock S3), a document record is created,
    and a processing job is queued via Celery.
    
    Form Parameters:
    - **file**: The document file (PDF, DOCX, etc.)
    - **deal_id**: Deal to associate document with
    - **file_type**: Document classification (CIM, NDA, Financial, Other)
    
    Returns the created document record with processing status.
    Raises 404 if deal not found.
    """
    # Validate deal exists
    deal = await DealService.get_deal_by_id(db, UUID(deal_id))
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {deal_id} not found"
        )
    
    # Generate S3 key (mock)
    s3_key = DocumentService.generate_s3_key(file.filename, UUID(deal_id))
    
    # Create document record
    document = await DocumentService.create_document(
        db, UUID(deal_id), file.filename, file_type, s3_key
    )
    
    # Publish upload event
    await publish_event("dealdesk:events", {
        "event": "document_uploaded",
        "document_id": str(document.id),
        "deal_id": deal_id,
        "filename": file.filename
    })
    
    return DocumentUploadResponse(
        document=document,
        message="Document uploaded successfully and queued for processing"
    )


@router.get("/{deal_id}", response_model=DocumentList)
async def list_deal_documents(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
) -> DocumentList:
    """
    List all documents for a deal.
    
    Path Parameters:
    - **deal_id**: Deal UUID
    
    Returns list of documents with status and metadata.
    """
    documents = await DocumentService.get_documents_by_deal(db, UUID(deal_id))
    return DocumentList(documents=documents, total=len(documents))


@router.get("/detail/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
) -> Document:
    """
    Get a specific document by ID.
    
    Path Parameters:
    - **document_id**: Document UUID
    
    Returns complete document details including analysis results.
    """
    document = await DocumentService.get_document_by_id(db, UUID(document_id))
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    return document


@router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Analyze a document using the DocumentAgent via SSE.
    
    The DocumentAgent reads the extracted text and returns:
    - Executive summary
    - Key risks with severity ratings
    - Key terms extraction
    - Document type classification
    
    Path Parameters:
    - **document_id**: Document to analyze
    
    SSE Events:
    - `progress`: Analysis progress updates
    - `result`: Complete analysis result
    - `done`: Analysis complete
    - `error`: Error message
    """
    
    # Get document
    document = await DocumentService.get_document_by_id(db, UUID(document_id))
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    # Mock extracted text if not available
    document_text = document.extracted_text or "Mock document content for analysis. This is a placeholder for actual extracted text from the uploaded document."
    
    async def event_generator():
        try:
            agent = DocumentAgent()
            
            # Progress updates
            yield f"event: progress\ndata: {json.dumps({'step': 'Reading document content...'})}\n\n"
            await asyncio.sleep(0.3)
            
            yield f"event: progress\ndata: {json.dumps({'step': 'Extracting key terms and conditions...'})}\n\n"
            await asyncio.sleep(0.3)
            
            yield f"event: progress\ndata: {json.dumps({'step': 'Identifying risk factors...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Run analysis
            result = await agent.analyze(
                document_id=document_id,
                document_text=document_text,
                filename=document.filename,
                file_type=document.file_type,
                streaming_callback=None
            )
            
            # Update document with analysis results
            await DocumentService.update_document_status(
                db,
                UUID(document_id),
                status="Ready",
                extracted_text=document_text,
                summary=result.get("summary"),
                key_risks=result.get("key_risks", []),
                key_terms=result.get("key_terms", {})
            )
            
            # Yield result
            yield f"event: result\ndata: {json.dumps(result)}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a document.
    
    Path Parameters:
    - **document_id**: Document UUID to delete
    
    Raises 404 if document not found.
    """
    deleted = await DocumentService.delete_document(db, UUID(document_id))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
