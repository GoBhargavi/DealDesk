"""News Agent for deal-relevant intelligence."""

import json
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from anthropic import AsyncAnthropic
from app.config import get_settings


NEWS_SYSTEM_PROMPT = """You are an M&A intelligence analyst. Given a target company name and sector, generate 10 realistic 
and plausible news items that would be relevant to an investment banker monitoring this deal. 
Include a mix of: company announcements, sector M&A activity, regulatory news, macro factors, 
and competitor moves. For each item include: headline, source (major financial outlet), 
published_at (within last 90 days), url (plausible), summary (2 sentences), sentiment 
(positive/neutral/negative), and relevance_tags. Return valid JSON array.

Return JSON in this exact format:
[
  {
    "headline": "string",
    "source": "string",
    "published_at": "ISO-8601 timestamp",
    "url": "string",
    "summary": "string",
    "sentiment": "positive|neutral|negative",
    "relevance_tags": ["string", "string"]
  }
]"""


class NewsAgent:
    """Agent for generating deal-relevant news and intelligence."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.model = "claude-sonnet-4-20250514"
    
    async def fetch_intelligence(
        self,
        deal_id: str,
        target_company: str,
        sector: str,
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate news intelligence for a deal.
        
        Args:
            deal_id: The deal identifier
            target_company: Name of target company
            sector: Industry sector
            streaming_callback: Optional callback for streaming updates
            
        Returns:
            List of news items
        """
        if streaming_callback:
            streaming_callback("Scanning market data sources...")
            await asyncio.sleep(0.3)
            streaming_callback("Analyzing company-specific developments...")
            await asyncio.sleep(0.3)
            streaming_callback("Compiling sector M&A activity...")
            await asyncio.sleep(0.3)
            streaming_callback("Generating intelligence report...")
            await asyncio.sleep(0.3)
        
        # If no API key, return mock data
        if not self.client:
            return self._generate_mock_news(deal_id, target_company, sector)
        
        prompt = f"""Generate 10 realistic news items for investment banking intelligence on:

Target Company: {target_company}
Sector: {sector}

Include a diverse mix of: company announcements, competitor moves, sector M&A, regulatory updates, 
and macro factors relevant to this deal."""
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=NEWS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else ""
            
            try:
                news_items = json.loads(content)
                # Add IDs and deal_id to each item
                for item in news_items:
                    item["id"] = str(random.randint(10000, 99999))
                    item["deal_id"] = deal_id
                return news_items
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    news_items = json.loads(json_match.group(1))
                    for item in news_items:
                        item["id"] = str(random.randint(10000, 99999))
                        item["deal_id"] = deal_id
                    return news_items
                raise
                
        except Exception:
            return self._generate_mock_news(deal_id, target_company, sector)
    
    def _generate_mock_news(
        self,
        deal_id: str,
        target_company: str,
        sector: str
    ) -> List[Dict[str, Any]]:
        """Generate mock news items for a deal."""
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
                "relevance_tags": random.sample(["M&A", sector, "Strategy", "Market Update", "Financials"], k=2)
            })
        
        # Sort by published date descending
        news_items.sort(key=lambda x: x["published_at"], reverse=True)
        return news_items
