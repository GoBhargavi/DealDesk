"""Pitchbook router for generating pitch book content."""

import json
import asyncio
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.deal_service import DealService
from app.services.redis_service import cache_set, cache_get
from app.agents.orchestrator import run_agent_task

router = APIRouter(prefix="/pitchbook", tags=["pitchbook"])


class PitchbookGenerateRequest(BaseModel):
    """Request body for pitchbook generation."""
    deal_id: str
    include_sections: List[str] = []


PITCHBOOK_SECTIONS = [
    "situation_overview",
    "company_profile",
    "valuation_analysis",
    "process_recommendations",
    "key_risks"
]


@router.post("/generate")
async def generate_pitchbook(
    request: PitchbookGenerateRequest,
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Generate pitch book content with streaming SSE output.
    
    The orchestrator runs multiple agents sequentially to generate
    each section of the pitch book, streaming results as they complete.
    
    Request Body:
    - **deal_id**: Deal identifier
    - **include_sections**: List of sections to generate (default: all)
      - situation_overview: Market context and strategic rationale
      - company_profile: Business description and financials
      - valuation_analysis: Comps summary and DCF range
      - process_recommendations: Buyer universe and timeline
      - key_risks: Top risks and mitigants
    
    SSE Events:
    - `section_start`: Beginning of section generation
    - `token`: Streaming content tokens
    - `section_done`: Section completion with full content
    - `done`: All sections complete
    - `error`: Error message if generation fails
    
    The generated pitchbook is cached and can be retrieved via GET /pitchbook/{deal_id}.
    """
    
    # Validate deal exists
    deal = await DealService.get_deal_by_id(db, UUID(request.deal_id))
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {request.deal_id} not found"
        )
    
    # Use all sections if none specified
    sections_to_generate = request.include_sections or PITCHBOOK_SECTIONS
    
    async def event_generator():
        try:
            # Get deal data for context
            deal_context = {
                "target_company": deal.target_company,
                "acquirer_company": deal.acquirer_company,
                "sector": deal.sector,
                "deal_type": deal.deal_type,
                "deal_value_usd": deal.deal_value_usd,
                "stage": deal.stage,
                "region": deal.region
            }
            
            # Run pitchbook agent through orchestrator
            result = await run_agent_task(
                task_type="pitchbook",
                deal_id=request.deal_id,
                input_data={
                    "deal_context": deal_context,
                    "include_sections": sections_to_generate
                },
                streaming_callback=None
            )
            
            pitchbook_sections = result.get("pitchbook", {})
            
            # Stream each section
            for section_name in sections_to_generate:
                if section_name in pitchbook_sections:
                    # Start section
                    yield f"event: section_start\ndata: {json.dumps({'section': section_name})}\n\n"
                    await asyncio.sleep(0.2)
                    
                    content = pitchbook_sections[section_name]
                    
                    # Stream tokens (simulate streaming by yielding in chunks)
                    words = content.split()
                    chunk_size = 5
                    for i in range(0, len(words), chunk_size):
                        chunk = " ".join(words[i:i+chunk_size])
                        yield f"event: token\ndata: {json.dumps({'section': section_name, 'token': chunk + ' '})}\n\n"
                        await asyncio.sleep(0.01)
                    
                    # Section complete
                    yield f"event: section_done\ndata: {json.dumps({'section': section_name, 'content': content})}\n\n"
                    await asyncio.sleep(0.3)
            
            # Cache the complete pitchbook
            cache_data = {
                "deal_id": request.deal_id,
                "sections": pitchbook_sections,
                "generated_at": result.get("generated_at")
            }
            await cache_set(f"pitchbook:{request.deal_id}", cache_data, expire=86400)
            
            # Done
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


@router.get("/{deal_id}")
async def get_pitchbook(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get cached pitch book for a deal.
    
    Path Parameters:
    - **deal_id**: Deal identifier
    
    Returns the cached pitch book sections if available.
    Raises 404 if no cached pitch book exists.
    """
    cached = await cache_get(f"pitchbook:{deal_id}")
    
    if not cached:
        # Check if deal exists
        deal = await DealService.get_deal_by_id(db, UUID(deal_id))
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deal with ID {deal_id} not found"
            )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached pitch book found for deal {deal_id}. Run POST /pitchbook/generate first."
        )
    
    return cached
