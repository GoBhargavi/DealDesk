"""
Research Agent for ad-hoc deep research queries.

A standalone agent that bankers can invoke directly from a deal page
for ad-hoc deep dives using the DeepSearchService.
"""

import logging
from typing import Optional, Dict, Any, Callable, Awaitable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.deep_search import deep_search_service, SearchResult

logger = logging.getLogger(__name__)


# Schema for research output
RESEARCH_OUTPUT_SCHEMA = {
    "query": "string - the original research question",
    "summary": "string - 3-4 paragraph narrative synthesizing findings",
    "key_findings": ["array of strings - bullet point key takeaways"],
    "sources": [
        {
            "url": "string",
            "title": "string",
            "source_name": "string",
            "published_date": "string or null",
            "relevance_score": "number"
        }
    ],
    "confidence": "string - 'high', 'medium', or 'low'",
    "caveats": "string or null - any limitations or warnings about the findings"
}


async def run_research_agent(
    query: str,
    deal_id: str,
    context: Dict[str, Any],
    llm: BaseChatModel,
    search_service,
    streaming_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """
    Run a standalone deep research agent.
    
    Takes a free-form research question and runs the full deep search pipeline,
    returning structured findings with sources, confidence level, and caveats.
    
    Args:
        query: Research question (e.g., "What is the regulatory landscape for healthcare data companies?")
        deal_id: Deal ID for context
        context: Additional context (company name, sector, deal type, etc.)
        llm: LangChain ChatModel for synthesis
        search_service: DeepSearchService instance
        streaming_callback: Async callback for SSE events
        
    Returns:
        Dict with keys: query, summary, key_findings, sources, confidence, caveats, data_source
    """
    logger.info(f"Starting research agent for deal {deal_id}: {query[:50]}...")
    
    try:
        # Run research through deep search service
        result = await search_service.research(
            task=query,
            context=context,
            output_schema=RESEARCH_OUTPUT_SCHEMA,
            llm=llm,
            streaming_callback=streaming_callback
        )
        
        # Ensure all required fields are present
        output = {
            "query": query,
            "summary": result.get("summary", "No summary generated"),
            "key_findings": result.get("key_findings", []),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", "low"),
            "caveats": result.get("caveats"),
            "data_source": result.get("data_source", "llm_generated"),
            "deal_id": deal_id
        }
        
        # Validate confidence level
        if output["confidence"] not in ["high", "medium", "low"]:
            output["confidence"] = "low"
        
        logger.info(f"Research agent completed for deal {deal_id}")
        return output
        
    except Exception as e:
        logger.error(f"Research agent failed for deal {deal_id}: {e}")
        
        # Emit error event if callback available
        if streaming_callback:
            await streaming_callback("agent_error", {
                "message": f"Research failed: {str(e)}",
                "code": "RESEARCH_ERROR"
            })
        
        # Return graceful error response
        return {
            "query": query,
            "summary": "Research could not be completed due to a technical error.",
            "key_findings": [],
            "sources": [],
            "confidence": "low",
            "caveats": f"Error: {str(e)}",
            "data_source": "error",
            "deal_id": deal_id
        }


async def run_quick_research(
    query: str,
    context: Dict[str, Any],
    llm: BaseChatModel,
    search_service
) -> str:
    """
    Quick research that returns a simple text summary without full pipeline.
    
    Useful for simple fact-checking or quick lookups.
    
    Args:
        query: Research question
        context: Additional context
        llm: Chat model
        search_service: DeepSearchService
        
    Returns:
        Text summary of findings
    """
    try:
        result = await search_service.research(
            task=query,
            context=context,
            output_schema={"summary": "string", "key_points": ["string"]},
            llm=llm,
            streaming_callback=None
        )
        
        summary = result.get("summary", "")
        key_points = result.get("key_points", [])
        
        if key_points:
            summary += "\n\nKey Points:\n" + "\n".join(f"• {p}" for p in key_points)
        
        if result.get("data_source") == "llm_generated":
            summary += "\n\n[Note: This response was generated using AI training data without live web research.]"
        
        return summary
        
    except Exception as e:
        logger.error(f"Quick research failed: {e}")
        return f"Could not complete research: {str(e)}"
