"""Celery worker for background document processing."""

import asyncio
from celery import Celery
from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "dealdesk",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.document_worker"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str, s3_key: str, file_type: str) -> dict:
    """
    Background task to process an uploaded document.
    
    This task:
    1. Downloads the file from S3 (mock)
    2. Extracts text using OCR/PDF parsing
    3. Updates document status in database
    4. Triggers document analysis if configured
    
    Args:
        document_id: UUID of the document to process
        s3_key: S3 key for file retrieval
        file_type: Document type classification
        
    Returns:
        Processing result with extracted text and status
    """
    try:
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={"step": "downloading", "progress": 10}
        )
        
        # Simulate download from S3
        asyncio.run(asyncio.sleep(0.5))
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "extracting_text", "progress": 40}
        )
        
        # Simulate text extraction
        # In production, use PyPDF2, pdfplumber, or OCR
        extracted_text = f"Mock extracted text for document {document_id}. "
        extracted_text += "This would contain the actual content extracted from the PDF. "
        extracted_text += f"Document type: {file_type}. S3 key: {s3_key}"
        
        asyncio.run(asyncio.sleep(1.0))
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "analyzing", "progress": 70}
        )
        
        # Mock analysis - would call DocumentAgent here
        summary = "Document processed successfully. Content extracted and ready for analysis."
        
        asyncio.run(asyncio.sleep(0.5))
        
        self.update_state(
            state="PROGRESS",
            meta={"step": "finalizing", "progress": 90}
        )
        
        # Update database (mock - would use async session in production)
        # async with AsyncSessionLocal() as session:
        #     await DocumentService.update_document_status(
        #         session, UUID(document_id), "Ready", extracted_text, summary
        #     )
        
        self.update_state(
            state="SUCCESS",
            meta={"step": "complete", "progress": 100}
        )
        
        return {
            "document_id": document_id,
            "status": "Ready",
            "extracted_length": len(extracted_text),
            "summary": summary
        }
        
    except Exception as exc:
        # Retry on failure
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc)}
        )
        
        return {
            "document_id": document_id,
            "status": "Error",
            "error": str(exc)
        }


@celery_app.task
def cleanup_old_documents(days: int = 30) -> dict:
    """
    Cleanup task to remove old processed documents.
    
    Args:
        days: Age threshold for cleanup
        
    Returns:
        Cleanup statistics
    """
    # Mock implementation
    return {
        "cleaned": 0,
        "days_threshold": days,
        "message": "Document cleanup completed"
    }


# Convenience function to queue document processing
def queue_document_processing(document_id: str, s3_key: str, file_type: str) -> str:
    """
    Queue a document for background processing.
    
    Args:
        document_id: Document UUID
        s3_key: S3 storage key
        file_type: Document classification
        
    Returns:
        Celery task ID
    """
    task = process_document.delay(document_id, s3_key, file_type)
    return task.id
