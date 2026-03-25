"""News Agent for deal-relevant intelligence with Deep Search."""

import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_factory import llm_factory
from app.services.deep_search import deep_search_service
from app.services.mcp_registry import mcp_registry


NEWS_SYSTEM_PROMPT = """You are an M&A intelligence analyst. Given real news articles and market data,
synthesize deal-relevant intelligence for investment bankers.

Analyze the provided sources and extract key insights about:
1. Company-specific developments relevant to M&A
2. Sector M&A activity and trends
3. Regulatory developments
4. Competitor moves
5. Macro factors affecting the deal

Return valid JSON array with each news item including:
- headline: concise headline
- source: publication name
- published_at: ISO-8601 timestamp
- url: article URL
- summary: 2-sentence summary
- sentiment: positive/neutral/negative
- relevance_tags: array of tag strings
- is_key_development: boolean for critical items

Return JSON in this exact format:
[
  {
    "headline": "string",
    "source": "string",
    "published_at": "ISO-8601 timestamp",
    "url": "string",
    "summary": "string",
    "sentiment": "positive|neutral|negative",
    "relevance_tags": ["string", "string"],
    "is_key_development": boolean
  }
]"""


# Schema for deep search output
NEWS_SEARCH_SCHEMA = {
    "news_items": [
        {
            "headline": "string - article headline",
            "source": "string - publication name",
            "published_date": "string - YYYY-MM-DD format",
            "url": "string - article URL",
            "summary": "string - brief summary",
            "sentiment": "string - positive/neutral/negative",
            "relevance_score": "number 0-1",
            "tags": ["array of relevance tags"]
        }
    ],
    "key_developments": ["array of strings describing major developments"],
    "market_sentiment": "string - overall sentiment summary"
}


class NewsAgent:
    """Agent for gathering deal-relevant news and intelligence using real web search."""
    
    async def fetch_intelligence(
        self,
        deal_id: str,
        target_company: str,
        sector: str,
        db: AsyncSession,
        streaming_callback: Optional[Callable[[str, Dict], Awaitable[None]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate news intelligence for a deal using real web search.
        
        Args:
            deal_id: The deal identifier
            target_company: Name of target company
            sector: Industry sector
            db: Database session for LLM and search config
            streaming_callback: Optional async callback for streaming updates
            
        Returns:
            List of news items with intelligence
        """
        try:
            # Get LLM for this agent
            llm = await llm_factory.get_llm_for_agent("news", db)
            
            # Check if MCP news service is available
            mcp_tools = mcp_registry.get_tools(["news"])
            
            # Prepare context
            context = {
                "target_company": target_company,
                "sector": sector,
                "deal_id": deal_id,
                "has_mcp_news": len(mcp_tools) > 0
            }
            
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "generating_queries",
                    "message": f"Searching for news about {target_company}..."
                })
            
            # Run deep search for real news
            search_result = await deep_search_service.research(
                task=f"Find recent news (last 90 days) about {target_company} and {sector} sector M&A activity. "
                     f"Include company announcements, competitor moves, regulatory developments, and market trends. "
                     f"Focus on items relevant to investment banking and M&A considerations.",
                context=context,
                output_schema=NEWS_SEARCH_SCHEMA,
                llm=llm,
                db=db,
                streaming_callback=streaming_callback
            )
            
            news_items = search_result.get("news_items", [])
            
            # If search returned results, process them
            if news_items:
                processed_items = []
                for i, item in enumerate(news_items[:15]):  # Limit to top 15
                    processed_items.append({
                        "id": str(10000 + i),
                        "deal_id": deal_id,
                        "headline": item.get("headline", "News Update"),
                        "source": item.get("source", "Financial News"),
                        "published_at": item.get("published_date", datetime.now().isoformat()),
                        "url": item.get("url", "#"),
                        "summary": item.get("summary", "No summary available"),
                        "sentiment": item.get("sentiment", "neutral"),
                        "relevance_tags": item.get("tags", [sector, "M&A"]),
                        "is_key_development": item.get("relevance_score", 0) > 0.8,
                        "data_source": "web_research"
                    })
                
                # Sort by relevance
                processed_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
                
                if streaming_callback:
                    await streaming_callback("research_done", {
                        "step": "done",
                        "source_count": len(processed_items),
                        "query_count": 5
                    })
                
                return processed_items
            
            # If no search results, fall back to generated sector intelligence
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "synthesising",
                    "message": "No recent news found. Generating sector intelligence..."
                })
            
            return await self._generate_intelligence_with_llm(deal_id, target_company, sector, llm)
            
        except Exception as e:
            # Return graceful error with fallback data
            if streaming_callback:
                await streaming_callback("agent_error", {
                    "message": f"News intelligence encountered an issue: {str(e)}. Using fallback data.",
                    "code": "NEWS_ERROR"
                })
            
            return self._generate_mock_news(deal_id, target_company, sector)
    
    async def _generate_intelligence_with_llm(
        self,
        deal_id: str,
        target_company: str,
        sector: str,
        llm: BaseChatModel
    ) -> List[Dict[str, Any]]:
        """Generate sector intelligence using LLM when web search has no results."""
        prompt = f"""Generate 8 realistic news intelligence items for investment banking on:

Target Company: {target_company}
Sector: {sector}

Note: No live news data was available. Generate sector-typical intelligence items that would
be relevant for M&A analysis, including typical developments seen in {sector} transactions.
Clearly mark these as "Sector Intelligence (AI-generated)" in the summary."""

        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=NEWS_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            # Extract JSON
            try:
                if "```" in content:
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                
                news_items = json.loads(content)
                
                # Add metadata
                for item in news_items:
                    item["id"] = str(random.randint(10000, 99999))
                    item["deal_id"] = deal_id
                    item["data_source"] = "llm_generated"
                    item["caveat"] = "Sector intelligence based on AI analysis (no live news data available)"
                
                return news_items[:10]
                
            except json.JSONDecodeError:
                return self._generate_mock_news(deal_id, target_company, sector)
                
        except Exception:
            return self._generate_mock_news(deal_id, target_company, sector)
    
    def _generate_mock_news(
        self,
        deal_id: str,
        target_company: str,
        sector: str
    ) -> List[Dict[str, Any]]:
        """Generate mock news items for a deal as fallback."""
        sources = ["Reuters", "Bloomberg", "Financial Times", "Wall Street Journal", 
                   "CNBC", "MarketWatch", "Forbes", "Business Insider"]
        sentiments = ["positive", "neutral", "negative"]
        sentiment_weights = [0.4, 0.4, 0.2]
        
        headlines = [
            f"{target_company} Announces Strategic Expansion into New Markets",
            f"{sector} Sector M&A Activity Accelerates in Q1 2025",
            f"{target_company} Reports Strong Q4 Results, Exceeding Expectations",
            f"Regulatory Review Process Begins for Major {sector} Transactions",
            f"{target_company} Appoints New Chief Financial Officer",
            f"{sector} Industry Outlook Remains Positive Despite Macro Headwinds",
            f"Competitor Analysis: How {target_company} Stacks Up in {sector}",
            f"Private Equity Interest in {sector} Reaches Multi-Year High",
            f"{target_company} Partners with Technology Provider for Digital Transformation",
            f"Market Volatility Creates Opportunities in {sector} M&A"
        ]
        
        news_items = []
        for i, headline in enumerate(headlines):
            days_ago = random.randint(1, 90)
            published = datetime.now() - timedelta(days=days_ago)
            sentiment = random.choices(sentiments, weights=sentiment_weights)[0]
            
            news_items.append({
                "id": str(10000 + i),
                "deal_id": deal_id,
                "headline": headline,
                "source": random.choice(sources),
                "published_at": published.isoformat(),
                "url": f"https://example.com/news/{deal_id}/{i}",
                "summary": f"Recent development regarding {target_company} and the broader {sector} sector. This update may have implications for ongoing M&A considerations.",
                "sentiment": sentiment,
                "relevance_tags": random.sample(["M&A", sector, "Strategy", "Market Update", "Financials"], k=2),
                "data_source": "llm_generated_fallback",
                "caveat": "Mock data used due to service unavailability"
            })
        
        # Sort by published date descending
        news_items.sort(key=lambda x: x["published_at"], reverse=True)
        return news_items
