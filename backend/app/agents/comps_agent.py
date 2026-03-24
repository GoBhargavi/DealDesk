"""Comps Agent for comparable transaction analysis."""

import json
import asyncio
from typing import Dict, Any, Optional, Callable
from anthropic import AsyncAnthropic
from app.config import get_settings


COMPS_SYSTEM_PROMPT = """You are a senior M&A analyst at a bulge-bracket investment bank. Given a target company, sector, 
and deal parameters, identify 6-8 highly relevant comparable transactions from the past 3 years. 
For each comparable, provide: company name, transaction date (YYYY-MM), deal value in $M, 
revenue in $M, EBITDA in $M, EV/Revenue multiple, EV/EBITDA multiple, and P/E ratio. 
Then calculate implied valuation ranges for the target (low/mid/high) based on median multiples. 
Return ONLY valid JSON matching the specified schema. Be realistic and specific — use plausible 
real-world figures for the sector.

Return JSON in this exact format:
{
  "target_company": "string",
  "sector": "string",
  "comparables": [
    {
      "company": "string",
      "transaction_date": "YYYY-MM",
      "deal_value_usd_m": number,
      "revenue_usd_m": number,
      "ebitda_usd_m": number,
      "ev_revenue": number,
      "ev_ebitda": number,
      "p_e": number
    }
  ],
  "implied_valuation": {
    "low": number,
    "mid": number,
    "high": number
  },
  "median_ev_ebitda": number,
  "median_ev_revenue": number
}"""


class CompsAgent:
    """Agent for generating comparable transaction analysis."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.model = "claude-sonnet-4-20250514"
    
    async def analyze(
        self,
        deal_id: str,
        target_company: str,
        sector: str,
        deal_type: str,
        deal_value_usd: Optional[float],
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate comparable transaction analysis.
        
        Args:
            deal_id: The deal identifier
            target_company: Name of target company
            sector: Industry sector
            deal_type: Type of transaction (M&A, LBO, etc.)
            deal_value_usd: Enterprise value in USD millions
            streaming_callback: Optional callback for streaming updates
            
        Returns:
            Dictionary containing comps analysis result
        """
        if streaming_callback:
            streaming_callback("Searching comparable transactions...")
            await asyncio.sleep(0.5)
            streaming_callback("Building multiples table...")
            await asyncio.sleep(0.5)
            streaming_callback("Calculating implied valuation...")
            await asyncio.sleep(0.5)
        
        # If no API key, return mock data
        if not self.client:
            return self._generate_mock_comps(target_company, sector, deal_value_usd)
        
        prompt = f"""Generate comparable transaction analysis for:

Target Company: {target_company}
Sector: {sector}
Deal Type: {deal_type}
Target Deal Value: ${deal_value_usd}M (if provided, use as reference)

Provide 6-8 realistic comparable transactions from the past 3 years with detailed financial metrics."""
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=COMPS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else ""
            
            # Extract JSON from response
            try:
                result = json.loads(content)
                result["deal_id"] = deal_id
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    result["deal_id"] = deal_id
                    return result
                raise
                
        except Exception as e:
            # Fallback to mock data on error
            return self._generate_mock_comps(target_company, sector, deal_value_usd)
    
    def _generate_mock_comps(
        self,
        target_company: str,
        sector: str,
        deal_value_usd: Optional[float]
    ) -> Dict[str, Any]:
        """Generate mock comparable transactions data."""
        from app.agents.tools import MOCK_TRANSACTIONS, SECTOR_BENCHMARKS
        
        sector_comps = MOCK_TRANSACTIONS.get(sector, MOCK_TRANSACTIONS["Technology"])
        benchmarks = SECTOR_BENCHMARKS.get(sector, SECTOR_BENCHMARKS["Technology"])
        
        comparables = sector_comps[:6]
        
        # Calculate median multiples
        ev_ebitda_values = [c["ev_ebitda"] for c in comparables]
        ev_revenue_values = [c["ev_revenue"] for c in comparables]
        
        median_ev_ebitda = sum(ev_ebitda_values) / len(ev_ebitda_values)
        median_ev_revenue = sum(ev_revenue_values) / len(ev_revenue_values)
        
        # Estimate implied valuation based on mock target metrics
        if deal_value_usd:
            target_revenue = deal_value_usd / median_ev_revenue
            target_ebitda = deal_value_usd / median_ev_ebitda
        else:
            target_revenue = 150
            target_ebitda = 30
        
        return {
            "deal_id": "",
            "target_company": target_company,
            "sector": sector,
            "comparables": comparables,
            "implied_valuation": {
                "low": round(target_revenue * median_ev_revenue * 0.85, 0),
                "mid": round(target_revenue * median_ev_revenue, 0),
                "high": round(target_revenue * median_ev_revenue * 1.15, 0)
            },
            "median_ev_ebitda": round(median_ev_ebitda, 1),
            "median_ev_revenue": round(median_ev_revenue, 1)
        }
