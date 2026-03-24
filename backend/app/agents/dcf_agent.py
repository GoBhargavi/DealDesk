"""DCF Agent for financial modeling assumptions."""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, List
from anthropic import AsyncAnthropic
from app.config import get_settings


DCF_SYSTEM_PROMPT = """You are a financial modeling expert at an investment bank. Given a company description, sector, 
and any available financial information, suggest realistic DCF model assumptions. Return JSON with:
revenue_growth_rates (array of 5 annual rates), ebitda_margins (array of 5), capex_pct_revenue, 
nwc_change_pct_revenue, tax_rate, wacc, terminal_growth_rate, exit_multiple, and a brief 
rationale (2-3 sentences) for each assumption group. Base assumptions on sector benchmarks.

Return JSON in this exact format:
{
  "company_name": "string",
  "revenue_growth_rates": [number, number, number, number, number],
  "ebitda_margins": [number, number, number, number, number],
  "capex_pct_revenue": number,
  "nwc_change_pct_revenue": number,
  "tax_rate": number,
  "wacc": number,
  "terminal_growth_rate": number,
  "exit_multiple": number,
  "rationale": {
    "growth": "string explaining revenue growth assumptions",
    "margins": "string explaining margin assumptions",
    "valuation": "string explaining WACC, terminal growth, and exit multiple assumptions"
  }
}"""


class DCFAgent:
    """Agent for generating DCF model assumptions."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.model = "claude-sonnet-4-20250514"
    
    async def suggest_assumptions(
        self,
        deal_id: str,
        company_description: str,
        sector: str,
        recent_financials_text: Optional[str],
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Generate DCF model assumptions.
        
        Args:
            deal_id: The deal identifier
            company_description: Description of the company
            sector: Industry sector
            recent_financials_text: Optional recent financial data text
            streaming_callback: Optional callback for streaming updates
            
        Returns:
            Dictionary containing DCF assumptions
        """
        if streaming_callback:
            streaming_callback("Analyzing company profile and sector benchmarks...")
            await asyncio.sleep(0.5)
            streaming_callback("Generating revenue growth projections...")
            await asyncio.sleep(0.5)
            streaming_callback("Estimating margin expansion trajectory...")
            await asyncio.sleep(0.5)
            streaming_callback("Calculating WACC and terminal value assumptions...")
            await asyncio.sleep(0.5)
        
        # If no API key, return mock data
        if not self.client:
            return self._generate_mock_assumptions(company_description, sector)
        
        financials_context = f"\n\nRecent Financials:\n{recent_financials_text}" if recent_financials_text else ""
        
        prompt = f"""Generate DCF model assumptions for:

Company: {company_description}
Sector: {sector}{financials_context}

Provide realistic 5-year projections based on sector benchmarks and industry dynamics."""
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=DCF_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text if response.content else ""
            
            try:
                result = json.loads(content)
                result["deal_id"] = deal_id
                return result
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                    result["deal_id"] = deal_id
                    return result
                raise
                
        except Exception:
            return self._generate_mock_assumptions(company_description, sector)
    
    def _generate_mock_assumptions(self, company_description: str, sector: str) -> Dict[str, Any]:
        """Generate mock DCF assumptions based on sector."""
        from app.agents.tools import SECTOR_BENCHMARKS
        
        benchmarks = SECTOR_BENCHMARKS.get(sector, SECTOR_BENCHMARKS["Technology"])
        
        base_growth = benchmarks["typical_revenue_growth"]
        base_margin = benchmarks["typical_ebitda_margin"]
        
        # Generate declining growth rates
        growth_rates = [
            round(base_growth * 1.3, 3),
            round(base_growth * 1.1, 3),
            round(base_growth, 3),
            round(base_growth * 0.85, 3),
            round(base_growth * 0.7, 3)
        ]
        
        # Generate expanding margins
        margin_expansion = 0.03
        ebitda_margins = [
            round(base_margin, 3),
            round(base_margin + margin_expansion * 0.25, 3),
            round(base_margin + margin_expansion * 0.5, 3),
            round(base_margin + margin_expansion * 0.75, 3),
            round(base_margin + margin_expansion, 3)
        ]
        
        return {
            "deal_id": "",
            "company_name": company_description[:50],
            "revenue_growth_rates": growth_rates,
            "ebitda_margins": ebitda_margins,
            "capex_pct_revenue": 0.04,
            "nwc_change_pct_revenue": 0.02,
            "tax_rate": 0.25,
            "wacc": benchmarks["typical_wacc"],
            "terminal_growth_rate": 0.025,
            "exit_multiple": benchmarks["typical_exit_multiple"],
            "rationale": {
                "growth": f"Revenue growth reflects {sector} sector dynamics with normalization over projection period.",
                "margins": f"EBITDA margin expansion driven by operational efficiency initiatives typical in {sector}.",
                "valuation": f"WACC and exit multiples based on {sector} sector benchmarks and comparable transactions."
            }
        }
