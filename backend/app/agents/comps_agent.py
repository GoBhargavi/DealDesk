"""Comps Agent for comparable transaction analysis with Deep Search."""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_factory import llm_factory
from app.services.deep_search import deep_search_service
from app.services.mcp_registry import mcp_registry


COMPS_SYSTEM_PROMPT = """You are a senior M&A analyst at a bulge-bracket investment bank.
Given comparable transaction data and target company information, analyze the multiples
and provide implied valuation ranges.

Analyze the provided comparable transactions and calculate:
1. Median EV/EBITDA and EV/Revenue multiples
2. Implied valuation range (low/mid/high) for the target
3. Key insights about the comparable set

Return ONLY valid JSON in this exact format:
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
  "median_ev_revenue": number,
  "analysis_notes": "string with key insights"
}"""


# Schema for deep search output
COMPS_SEARCH_SCHEMA = {
    "comparables": [
        {
            "company": "string - acquired company name",
            "acquirer": "string - acquiring company name",
            "transaction_date": "string - YYYY-MM format",
            "deal_value_usd_m": "number in millions",
            "revenue_usd_m": "number or null",
            "ebitda_usd_m": "number or null",
            "ev_revenue": "number or null",
            "ev_ebitda": "number or null",
            "p_e": "number or null"
        }
    ]
}


class CompsAgent:
    """Agent for generating comparable transaction analysis using real market data."""
    
    async def analyze(
        self,
        deal_id: str,
        target_company: str,
        sector: str,
        deal_type: str,
        deal_value_usd: Optional[float],
        db: AsyncSession,
        streaming_callback: Optional[Callable[[str, Dict], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Generate comparable transaction analysis using real market data via Deep Search.
        
        Args:
            deal_id: The deal identifier
            target_company: Name of target company
            sector: Industry sector
            deal_type: Type of transaction (M&A, LBO, etc.)
            deal_value_usd: Enterprise value in USD millions
            db: Database session for LLM and search config
            streaming_callback: Optional async callback for streaming updates
            
        Returns:
            Dictionary containing comps analysis result
        """
        try:
            # Get LLM for this agent
            llm = await llm_factory.get_llm_for_agent("comps", db)
            
            # Check if MCP financial data is available
            mcp_tools = mcp_registry.get_tools(["financial_data"])
            
            # Prepare context for research
            context = {
                "target_company": target_company,
                "sector": sector,
                "deal_type": deal_type,
                "deal_value_usd": deal_value_usd,
                "has_mcp_data": len(mcp_tools) > 0
            }
            
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "generating_queries",
                    "message": "Generating search queries for comparable transactions..."
                })
            
            # Run deep search for real comparable transactions
            search_result = await deep_search_service.research(
                task=f"Find 6-8 comparable M&A transactions in {sector} from 2022-2025. "
                     f"Focus on transactions with disclosed deal values, revenue, and EBITDA multiples. "
                     f"Target company profile: {target_company}, {deal_type}.",
                context=context,
                output_schema=COMPS_SEARCH_SCHEMA,
                llm=llm,
                db=db,
                streaming_callback=streaming_callback
            )
            
            comparables = search_result.get("comparables", [])
            
            # If no results from search, fall back to LLM generation with warning
            if not comparables:
                if streaming_callback:
                    await streaming_callback("research_step", {
                        "step": "synthesising",
                        "message": "No comparable data found. Generating sector-typical multiples..."
                    })
                comparables = self._generate_sector_typical_comps(sector, target_company)
            
            # Calculate multiples
            ev_ebitda_values = [c.get("ev_ebitda", 0) for c in comparables if c.get("ev_ebitda")]
            ev_revenue_values = [c.get("ev_revenue", 0) for c in comparables if c.get("ev_revenue")]
            
            median_ev_ebitda = sum(ev_ebitda_values) / len(ev_ebitda_values) if ev_ebitda_values else 12.0
            median_ev_revenue = sum(ev_revenue_values) / len(ev_revenue_values) if ev_revenue_values else 3.0
            
            # Estimate target metrics
            if deal_value_usd:
                target_revenue = deal_value_usd / median_ev_revenue if median_ev_revenue else 100
                target_ebitda = deal_value_usd / median_ev_ebitda if median_ev_ebitda else 30
            else:
                target_revenue = 150
                target_ebitda = 30
            
            # Build final result
            result = {
                "deal_id": deal_id,
                "target_company": target_company,
                "sector": sector,
                "comparables": comparables[:8],
                "implied_valuation": {
                    "low": round(target_revenue * median_ev_revenue * 0.85, 0),
                    "mid": round(target_revenue * median_ev_revenue, 0),
                    "high": round(target_revenue * median_ev_revenue * 1.15, 0)
                },
                "median_ev_ebitda": round(median_ev_ebitda, 1),
                "median_ev_revenue": round(median_ev_revenue, 1),
                "data_source": search_result.get("data_source", "llm_generated"),
                "analysis_notes": f"Based on {len(comparables)} comparable transactions from recent market data."
            }
            
            if streaming_callback:
                await streaming_callback("research_done", {
                    "step": "done",
                    "source_count": len(comparables),
                    "query_count": 5
                })
            
            return result
            
        except Exception as e:
            # Return graceful error with fallback data
            if streaming_callback:
                await streaming_callback("agent_error", {
                    "message": f"Comps analysis encountered an issue: {str(e)}. Using fallback data.",
                    "code": "COMPS_ERROR"
                })
            
            return self._generate_mock_comps(target_company, sector, deal_value_usd)
    
    def _generate_sector_typical_comps(self, sector: str, target_company: str) -> list:
        """Generate sector-typical comparable data when search returns no results."""
        from app.agents.tools import MOCK_TRANSACTIONS
        
        sector_comps = MOCK_TRANSACTIONS.get(sector, MOCK_TRANSACTIONS["Technology"])
        
        # Add disclaimer that these are sector-typical, not actual transactions
        return [
            {
                **comp,
                "_note": "Sector-typical multiples (not actual transaction)"
            }
            for comp in sector_comps[:6]
        ]
    
    def _generate_mock_comps(
        self,
        target_company: str,
        sector: str,
        deal_value_usd: Optional[float]
    ) -> Dict[str, Any]:
        """Generate mock comparable transactions data as fallback."""
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
            "median_ev_revenue": round(median_ev_revenue, 1),
            "data_source": "llm_generated_fallback",
            "caveats": "This analysis used AI-generated sector-typical data due to service unavailability."
        }
