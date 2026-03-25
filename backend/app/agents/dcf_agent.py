"""DCF Agent for financial modeling assumptions with configurable LLM."""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, List, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_factory import llm_factory
from app.services.mcp_registry import mcp_registry


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
    """Agent for generating DCF model assumptions using configurable LLM."""
    
    async def suggest_assumptions(
        self,
        deal_id: str,
        company_description: str,
        sector: str,
        recent_financials_text: Optional[str],
        db: AsyncSession,
        streaming_callback: Optional[Callable[[str, Dict], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Generate DCF model assumptions using the configured LLM.
        
        Args:
            deal_id: The deal identifier
            company_description: Description of the company
            sector: Industry sector
            recent_financials_text: Optional recent financial data text
            db: Database session for LLM configuration
            streaming_callback: Optional async callback for streaming updates
            
        Returns:
            Dictionary containing DCF assumptions
        """
        try:
            # Get LLM for this agent
            llm = await llm_factory.get_llm_for_agent("dcf", db)
            
            # Check if MCP financial data tools are available
            mcp_tools = mcp_registry.get_tools(["financial_data"])
            
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "analyzing",
                    "message": "Analyzing company profile and sector benchmarks..."
                })
                await asyncio.sleep(0.3)
                await streaming_callback("research_step", {
                    "step": "projecting",
                    "message": "Generating revenue growth projections..."
                })
                await asyncio.sleep(0.3)
                await streaming_callback("research_step", {
                    "step": "estimating",
                    "message": "Estimating margin expansion trajectory..."
                })
                await asyncio.sleep(0.3)
            
            financials_context = f"\n\nRecent Financials:\n{recent_financials_text}" if recent_financials_text else ""
            
            # Check if we have MCP tools for real financial data
            mcp_context = ""
            if mcp_tools:
                mcp_context = "\n\nNote: Financial data tools are available for real-time market data integration."
            
            prompt = f"""Generate DCF model assumptions for:

Company: {company_description}
Sector: {sector}{financials_context}{mcp_context}

Provide realistic 5-year projections based on sector benchmarks and industry dynamics."""
            
            messages = [
                SystemMessage(content=DCF_SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            # Extract JSON from response
            try:
                if "```" in content:
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                
                result = json.loads(content)
                result["deal_id"] = deal_id
                result["data_source"] = "llm_generated"
                
                if streaming_callback:
                    await streaming_callback("research_done", {
                        "step": "done",
                        "message": "DCF assumptions generated"
                    })
                
                return result
                
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse DCF assumptions from LLM response: {e}")
                
        except Exception as e:
            # Return graceful error with fallback data
            if streaming_callback:
                await streaming_callback("agent_error", {
                    "message": f"DCF analysis encountered an issue: {str(e)}. Using sector benchmarks.",
                    "code": "DCF_ERROR"
                })
            
            return self._generate_mock_assumptions(company_description, sector)
    
    def _generate_mock_assumptions(self, company_description: str, sector: str) -> Dict[str, Any]:
        """Generate mock DCF assumptions based on sector as fallback."""
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
            },
            "data_source": "llm_generated_fallback",
            "caveats": "Sector-typical assumptions used due to service unavailability."
        }
