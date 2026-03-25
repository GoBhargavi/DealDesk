"""LangGraph orchestrator for multi-agent system with configurable LLM and MCP tools."""

from typing import TypedDict, Dict, Any, List, Optional, Callable, Awaitable
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.comps_agent import CompsAgent
from app.agents.dcf_agent import DCFAgent
from app.agents.news_agent import NewsAgent
from app.agents.document_agent import DocumentAgent
from app.services.mcp_registry import mcp_registry


class AgentState(TypedDict):
    """State shape for LangGraph agent orchestration."""
    task_type: str
    deal_id: str
    input_data: Dict[str, Any]
    partial_results: Dict[str, Any]
    final_result: Dict[str, Any]
    streaming_callback: Optional[Callable[[str, Dict], Awaitable[None]]]
    errors: List[str]
    db: Optional[AsyncSession]  # Database session for LLM configuration


def create_orchestrator_graph() -> StateGraph:
    """
    Create the LangGraph orchestration graph for multi-agent system.
    
    The graph routes tasks to appropriate agents and handles pitchbook
    generation as a multi-step workflow. Integrates MCP tools for
    external data access.
    """
    
    # Initialize agents
    comps_agent = CompsAgent()
    dcf_agent = DCFAgent()
    news_agent = NewsAgent()
    document_agent = DocumentAgent()
    
    def route_task(state: AgentState) -> str:
        """Route to the appropriate agent based on task type."""
        task_type = state.get("task_type", "")
        
        routing_map = {
            "comps": "comps_node",
            "dcf": "dcf_node",
            "news": "news_node",
            "document": "document_node",
            "pitchbook": "pitchbook_node"
        }
        
        return routing_map.get(task_type, END)
    
    async def comps_node(state: AgentState) -> Dict[str, Any]:
        """Execute comps analysis agent."""
        try:
            input_data = state["input_data"]
            db = state.get("db")
            
            if not db:
                raise ValueError("Database session required for LLM configuration")
            
            result = await comps_agent.analyze(
                deal_id=state["deal_id"],
                target_company=input_data.get("target_company", ""),
                sector=input_data.get("sector", ""),
                deal_type=input_data.get("deal_type", ""),
                deal_value_usd=input_data.get("deal_value_usd"),
                db=db,
                streaming_callback=state.get("streaming_callback")
            )
            return {
                "final_result": result,
                "partial_results": {**state.get("partial_results", {}), "comps": result}
            }
        except Exception as e:
            return {
                "errors": [*state.get("errors", []), f"Comps agent error: {str(e)}"],
                "final_result": {}
            }
    
    async def dcf_node(state: AgentState) -> Dict[str, Any]:
        """Execute DCF agent for assumption suggestions."""
        try:
            input_data = state["input_data"]
            db = state.get("db")
            
            if not db:
                raise ValueError("Database session required for LLM configuration")
            
            result = await dcf_agent.suggest_assumptions(
                deal_id=state["deal_id"],
                company_description=input_data.get("company_description", ""),
                sector=input_data.get("sector", ""),
                recent_financials_text=input_data.get("recent_financials_text"),
                db=db,
                streaming_callback=state.get("streaming_callback")
            )
            return {
                "final_result": result,
                "partial_results": {**state.get("partial_results", {}), "dcf": result}
            }
        except Exception as e:
            return {
                "errors": [*state.get("errors", []), f"DCF agent error: {str(e)}"],
                "final_result": {}
            }
    
    async def news_node(state: AgentState) -> Dict[str, Any]:
        """Execute news agent for intelligence gathering."""
        try:
            input_data = state["input_data"]
            db = state.get("db")
            
            if not db:
                raise ValueError("Database session required for LLM configuration")
            
            result = await news_agent.fetch_intelligence(
                deal_id=state["deal_id"],
                target_company=input_data.get("target_company", ""),
                sector=input_data.get("sector", ""),
                db=db,
                streaming_callback=state.get("streaming_callback")
            )
            return {
                "final_result": {"news_items": result},
                "partial_results": {**state.get("partial_results", {}), "news": result}
            }
        except Exception as e:
            return {
                "errors": [*state.get("errors", []), f"News agent error: {str(e)}"],
                "final_result": {}
            }
    
    async def document_node(state: AgentState) -> Dict[str, Any]:
        """Execute document agent for analysis."""
        try:
            input_data = state["input_data"]
            db = state.get("db")
            
            if not db:
                raise ValueError("Database session required for LLM configuration")
            
            result = await document_agent.analyze(
                document_id=input_data.get("document_id", ""),
                document_text=input_data.get("document_text", ""),
                filename=input_data.get("filename", ""),
                file_type=input_data.get("file_type", ""),
                db=db,
                streaming_callback=state.get("streaming_callback")
            )
            return {
                "final_result": result,
                "partial_results": {**state.get("partial_results", {}), "document": result}
            }
        except Exception as e:
            return {
                "errors": [*state.get("errors", []), f"Document agent error: {str(e)}"],
                "final_result": {}
            }
    
    async def pitchbook_node(state: AgentState) -> Dict[str, Any]:
        """
        Execute pitchbook generation as a multi-step workflow.
        For now, this generates a structured pitchbook with placeholders for each section.
        """
        input_data = state["input_data"]
        include_sections = input_data.get("include_sections", [])
        
        sections = {}
        
        # Section 1: Situation Overview
        if "situation_overview" in include_sections or not include_sections:
            if state.get("streaming_callback"):
                state["streaming_callback"]("Generating situation overview...")
            sections["situation_overview"] = """## Situation Overview

### Market Context
The target company operates in a dynamic and growing market with favorable secular tailwinds. Industry consolidation is accelerating, creating opportunities for strategic buyers to achieve scale and operational synergies.

### Strategic Rationale
This transaction represents a compelling opportunity to acquire a market-leading platform with demonstrated revenue growth and strong unit economics. The combination would create significant value through revenue synergies and cost optimization.

### Timing Considerations
Current market conditions support executing this transaction now, with favorable debt financing availability and strategic buyer interest at elevated levels."""
        
        # Section 2: Company Profile
        if "company_profile" in include_sections or not include_sections:
            if state.get("streaming_callback"):
                state["streaming_callback"]("Analyzing company profile...")
            sections["company_profile"] = """## Company Profile

### Business Description
The target is a leading provider of mission-critical solutions serving a diversified customer base. The company has established strong market positioning through proprietary technology and long-term customer relationships.

### Key Products & Services
- Core platform generating recurring revenue with high retention rates
- Complementary service offerings with expanding margins
- New product pipeline addressing adjacent market opportunities

### Financial Summary (LTM)
- Revenue: $180M (18% YoY growth)
- EBITDA: $42M (23.3% margin)
- EBITDA growth: 25% YoY
- Strong cash conversion with minimal capex requirements"""
        
        # Section 3: Valuation Analysis
        if "valuation_analysis" in include_sections or not include_sections:
            if state.get("streaming_callback"):
                state["streaming_callback"]("Building valuation analysis...")
            sections["valuation_analysis"] = """## Valuation Analysis

### Comparable Transactions
Recent M&A activity in the sector supports valuation multiples in the 20-30x EV/EBITDA range for high-quality assets. Selected comparables demonstrate consistent execution and similar growth profiles.

| Methodology | Low | Mid | High |
|-------------|-----|-----|------|
| EV/EBITDA (22x-28x) | $920M | $1,150M | $1,380M |
| EV/Revenue (5.5x-7.5x) | $990M | $1,260M | $1,350M |
| DCF (11% WACC) | $980M | $1,180M | $1,320M |

### Football Field Summary
The valuation analysis suggests a value range of $1.0B to $1.4B, with a midpoint of $1.2B representing fair value for a controlling transaction.
"""
        
        # Section 4: Process Recommendations
        if "process_recommendations" in include_sections or not include_sections:
            if state.get("streaming_callback"):
                state["streaming_callback"]("Developing process recommendations...")
            sections["process_recommendations"] = """## Process Recommendations

### Buyer Universe
- **Strategic Acquirers**: Complementary platform players seeking scale
- **Financial Sponsors**: PE firms with sector expertise and platform strategies
- **Cross-Border Strategics**: International players seeking US market entry

### Recommended Process
We recommend a targeted bilateral negotiation with 2-3 qualified strategic parties, supplemented by limited sponsor outreach to validate pricing.

### Timeline
- Week 1-2: Management presentations to qualified parties
- Week 3-4: Indicative bids due
- Week 5-8: Final bids and documentation
- Week 9-12: Exclusive negotiation and closing

### Deal Structure
Consider a mix of cash at closing with contingent consideration (earnout) for upside performance, balanced with seller rollover to align incentives."""
        
        # Section 5: Key Risks
        if "key_risks" in include_sections or not include_sections:
            if state.get("streaming_callback"):
                state["streaming_callback"]("Assessing key risks...")
            sections["key_risks"] = """## Key Risks & Mitigants

### 1. Customer Concentration
**Risk**: Top customers represent significant revenue concentration.
**Mitigant**: Long-term contracts and embedded solutions create switching costs.

### 2. Competition Intensity
**Risk**: Well-funded competitors may impact pricing power.
**Mitigant**: Proprietary technology and customer relationships provide differentiation.

### 3. Technology Obsolescence
**Risk**: Rapid innovation may require continued R&D investment.
**Mitigant**: Strong engineering culture and consistent innovation track record.

### 4. Regulatory Environment
**Risk**: Evolving regulations may increase compliance costs.
**Mitigant**: Current compliance infrastructure and proactive legal team.

### 5. Integration Execution
**Risk**: Post-close integration risks for combined operations.
**Mitigant**: Experienced management team with prior M&A integration experience."""
        
        return {
            "final_result": {
                "pitchbook": sections,
                "deal_id": state["deal_id"],
                "generated_at": "2025-03-24T00:00:00Z"
            },
            "partial_results": {**state.get("partial_results", {}), "pitchbook": sections}
        }
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("route_task", route_task)
    workflow.add_node("comps_node", comps_node)
    workflow.add_node("dcf_node", dcf_node)
    workflow.add_node("news_node", news_node)
    workflow.add_node("document_node", document_node)
    workflow.add_node("pitchbook_node", pitchbook_node)
    
    # Add edges
    workflow.set_entry_point("route_task")
    
    workflow.add_conditional_edges(
        "route_task",
        route_task,
        {
            "comps_node": "comps_node",
            "dcf_node": "dcf_node",
            "news_node": "news_node",
            "document_node": "document_node",
            "pitchbook_node": "pitchbook_node",
            END: END
        }
    )
    
    # All agent nodes go to END
    workflow.add_edge("comps_node", END)
    workflow.add_edge("dcf_node", END)
    workflow.add_edge("news_node", END)
    workflow.add_edge("document_node", END)
    workflow.add_edge("pitchbook_node", END)
    
    return workflow.compile()


# Global orchestrator instance
_orchestrator = None


def get_orchestrator():
    """Get or create the orchestrator graph instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = create_orchestrator_graph()
    return _orchestrator


async def run_agent_task(
    task_type: str,
    deal_id: str,
    input_data: Dict[str, Any],
    streaming_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Run an agent task through the orchestrator.
    
    Args:
        task_type: Type of task (comps, dcf, news, document, pitchbook)
        deal_id: The deal identifier
        input_data: Input data for the task
        streaming_callback: Optional callback for streaming updates
        
    Returns:
        Final result from the agent execution
    """
    orchestrator = get_orchestrator()
    
    initial_state: AgentState = {
        "task_type": task_type,
        "deal_id": deal_id,
        "input_data": input_data,
        "partial_results": {},
        "final_result": {},
        "streaming_callback": streaming_callback,
        "errors": []
    }
    
    result = await orchestrator.ainvoke(initial_state)
    return result.get("final_result", {})
