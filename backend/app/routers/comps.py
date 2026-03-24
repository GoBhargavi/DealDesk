"""Comps router for comparable transaction analysis."""

import json
import asyncio
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.deal_service import DealService
from app.services.redis_service import cache_set, cache_get
from app.agents.orchestrator import run_agent_task

router = APIRouter(prefix="/comps", tags=["comps"])


class CompsAnalyzeRequest(BaseModel):
    """Request body for comps analysis."""
    deal_id: str
    target_company: str
    sector: str
    deal_type: str
    deal_value_usd: Optional[float] = None


@router.post("/analyze")
async def analyze_comps(
    request: CompsAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Run comps analysis with streaming SSE output.
    
    This endpoint triggers the CompsAgent to analyze comparable transactions
    and returns results via Server-Sent Events (SSE).
    
    Request Body:
    - **deal_id**: Deal identifier for context
    - **target_company**: Name of target company
    - **sector**: Industry sector for finding comparables
    - **deal_type**: Transaction type (M&A, LBO, etc.)
    - **deal_value_usd**: Optional enterprise value reference
    
    SSE Events:
    - `reasoning`: Agent reasoning step updates
    - `result`: Final JSON comps table
    - `error`: Error message if analysis fails
    - `done`: Stream completion indicator
    
    The result is cached and can be retrieved via GET /comps/{deal_id}.
    """
    
    async def event_generator():
        reasoning_steps = []
        
        def streaming_callback(step: str):
            reasoning_steps.append(step)
        
        try:
            # Yield initial reasoning
            yield f"event: reasoning\ndata: {json.dumps({'step': 'Initializing analysis...'})}\n\n"
            await asyncio.sleep(0.3)
            
            yield f"event: reasoning\ndata: {json.dumps({'step': 'Searching comparable transactions...'})}\n\n"
            await asyncio.sleep(0.3)
            
            yield f"event: reasoning\ndata: {json.dumps({'step': 'Building multiples table...'})}\n\n"
            await asyncio.sleep(0.3)
            
            yield f"event: reasoning\ndata: {json.dumps({'step': 'Calculating implied valuation...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Run the agent
            result = await run_agent_task(
                task_type="comps",
                deal_id=request.deal_id,
                input_data={
                    "target_company": request.target_company,
                    "sector": request.sector,
                    "deal_type": request.deal_type,
                    "deal_value_usd": request.deal_value_usd
                },
                streaming_callback=streaming_callback
            )
            
            result["deal_id"] = request.deal_id
            
            # Cache the result
            await cache_set(f"comps:{request.deal_id}", result, expire=86400)
            
            # Yield final result
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


@router.get("/{deal_id}")
async def get_cached_comps(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get cached comps result for a deal.
    
    Path Parameters:
    - **deal_id**: Deal identifier
    
    Returns the cached comps analysis result if available.
    Raises 404 if no cached result exists.
    """
    cached = await cache_get(f"comps:{deal_id}")
    
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
            detail=f"No cached comps analysis found for deal {deal_id}. Run POST /comps/analyze first."
        )
    
    return cached
