"""News router for deal-relevant intelligence."""

import json
import asyncio
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.deal_service import DealService
from app.agents.orchestrator import run_agent_task

router = APIRouter(prefix="/news", tags=["news"])


class NewsItem(BaseModel):
    """News item schema."""
    id: str
    headline: str
    source: str
    published_at: str
    url: str
    summary: str
    sentiment: str
    relevance_tags: List[str]
    deal_id: Optional[str] = None


class NewsFetchRequest(BaseModel):
    """Request to fetch news for a deal."""
    deal_id: str


# Mock news database (in-memory for demo)
_mock_news_db: List[dict] = []


def _generate_mock_news() -> List[dict]:
    """Generate a diverse set of mock news items."""
    if _mock_news_db:
        return _mock_news_db
    
    from datetime import datetime, timedelta
    import random
    
    sources = ["Reuters", "Bloomberg", "Financial Times", "Wall Street Journal", 
               "CNBC", "MarketWatch", "Forbes", "TechCrunch", "Business Insider"]
    sentiments = ["positive", "neutral", "negative"]
    
    headlines = [
        "M&A Activity Accelerates in Technology Sector as Valuations Stabilize",
        "Private Equity Firms Eye Healthcare Assets Amid Sector Consolidation",
        "Regulatory Review Process Extended for Large Cross-Border Transactions",
        "Energy Sector Sees Renewed Interest from Strategic Acquirers",
        "Fintech Valuations Rebound Following Market Correction",
        "European Markets Open to US Strategic Buyers",
        "Antitrust Concerns Rise in Big Tech Acquisitions",
        "Industrials M&A Driven by Supply Chain Reshoring Trends",
        "Consumer Sector Faces Headwinds from Inflation Pressures",
        "Credit Markets Support LBO Financing at Improved Terms",
        "SPAC Market Activity Declines as Traditional M&A Picks Up",
        "Cross-Border Deal Flow Reaches Pre-Pandemic Levels",
        "Technology Companies Pursue Vertical Integration Strategies",
        "Healthcare Innovation Drives Strategic Acquisition Interest",
        "ESG Considerations Increasingly Factor into M&A Decisions"
    ]
    
    for i, headline in enumerate(headlines):
        days_ago = random.randint(1, 90)
        published = datetime.now() - timedelta(days=days_ago)
        sentiment = random.choice(sentiments)
        
        _mock_news_db.append({
            "id": str(10000 + i),
            "headline": headline,
            "source": random.choice(sources),
            "published_at": published.isoformat(),
            "url": f"https://example.com/news/{10000 + i}",
            "summary": f"This article discusses {headline.lower()} and implications for investment banking activity.",
            "sentiment": sentiment,
            "relevance_tags": random.sample(["M&A", "Technology", "Healthcare", "Financials", "Market Update", "Strategy"], k=2),
            "deal_id": None
        })
    
    # Sort by date
    _mock_news_db.sort(key=lambda x: x["published_at"], reverse=True)
    return _mock_news_db


@router.get("")
async def list_news(
    q: Optional[str] = Query(None, description="Search query"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    deal_id: Optional[str] = Query(None, description="Filter by deal ID"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
) -> dict:
    """
    List news items with filtering and pagination.
    
    Query Parameters:
    - **q**: Search query for headline or summary
    - **sector**: Filter by relevant sector tag
    - **deal_id**: Filter by deal-specific news
    - **sentiment**: Filter by sentiment (positive, neutral, negative)
    - **page**: Page number (1-indexed)
    - **page_size**: Items per page
    
    Returns paginated list of news items.
    """
    news = _generate_mock_news()
    
    # Apply filters
    if q:
        q_lower = q.lower()
        news = [n for n in news if q_lower in n["headline"].lower() or q_lower in n["summary"].lower()]
    
    if sector:
        news = [n for n in news if sector in n["relevance_tags"]]
    
    if sentiment:
        news = [n for n in news if n["sentiment"] == sentiment]
    
    if deal_id:
        news = [n for n in news if n.get("deal_id") == deal_id]
    
    # Paginate
    total = len(news)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_news = news[start:end]
    
    return {
        "items": paginated_news,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/fetch-for-deal")
async def fetch_news_for_deal(
    request: NewsFetchRequest,
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Fetch news intelligence specific to a deal via SSE.
    
    The NewsAgent searches for news relevant to the deal's target
    company and sector, returning results as they are found.
    
    Request Body:
    - **deal_id**: Deal to fetch intelligence for
    
    SSE Events:
    - `progress`: Agent progress updates
    - `news_item`: Individual news items as found
    - `done`: Search complete
    - `error`: Error message
    
    News items are associated with the deal and can be retrieved
    via GET /news?deal_id={deal_id}.
    """
    
    # Validate deal exists
    deal = await DealService.get_deal_by_id(db, UUID(request.deal_id))
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {request.deal_id} not found"
        )
    
    async def event_generator():
        try:
            # Progress updates
            yield f"event: progress\ndata: {json.dumps({'step': 'Scanning market data sources...'})}\n\n"
            await asyncio.sleep(0.3)
            
            yield f"event: progress\ndata: {json.dumps({'step': 'Analyzing company-specific developments...'})}\n\n"
            await asyncio.sleep(0.3)
            
            yield f"event: progress\ndata: {json.dumps({'step': 'Compiling sector M&A activity...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Run news agent
            result = await run_agent_task(
                task_type="news",
                deal_id=request.deal_id,
                input_data={
                    "target_company": deal.target_company,
                    "sector": deal.sector
                },
                streaming_callback=None
            )
            
            news_items = result.get("news_items", [])
            
            # Yield each news item
            for item in news_items:
                yield f"event: news_item\ndata: {json.dumps(item)}\n\n"
                await asyncio.sleep(0.1)
            
            # Store in mock DB (associate with deal)
            for item in news_items:
                item["deal_id"] = request.deal_id
                _mock_news_db.insert(0, item)
            
            yield f"event: done\ndata: {json.dumps({'count': len(news_items)})}\n\n"
            
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
