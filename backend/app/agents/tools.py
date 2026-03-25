"""LangChain tools for M&A agents with MCP integration."""

from typing import Dict, List, Any, Optional
from langchain.tools import tool

from app.services.mcp_registry import mcp_registry


SECTOR_BENCHMARKS = {
    "Technology": {
        "typical_ebitda_margin": 0.25,
        "typical_revenue_growth": 0.15,
        "typical_wacc": 0.11,
        "typical_exit_multiple": 18.0,
        "median_ev_ebitda": 22.0,
        "median_ev_revenue": 6.5
    },
    "Healthcare": {
        "typical_ebitda_margin": 0.22,
        "typical_revenue_growth": 0.10,
        "typical_wacc": 0.10,
        "typical_exit_multiple": 16.0,
        "median_ev_ebitda": 18.0,
        "median_ev_revenue": 4.5
    },
    "Energy": {
        "typical_ebitda_margin": 0.35,
        "typical_revenue_growth": 0.05,
        "typical_wacc": 0.09,
        "typical_exit_multiple": 8.0,
        "median_ev_ebitda": 8.5,
        "median_ev_revenue": 2.0
    },
    "Financials": {
        "typical_ebitda_margin": 0.45,
        "typical_revenue_growth": 0.08,
        "typical_wacc": 0.10,
        "typical_exit_multiple": 12.0,
        "median_ev_ebitda": 12.0,
        "median_ev_revenue": 3.5
    },
    "Industrials": {
        "typical_ebitda_margin": 0.15,
        "typical_revenue_growth": 0.05,
        "typical_wacc": 0.095,
        "typical_exit_multiple": 10.0,
        "median_ev_ebitda": 9.5,
        "median_ev_revenue": 1.8
    },
    "Consumer": {
        "typical_ebitda_margin": 0.12,
        "typical_revenue_growth": 0.04,
        "typical_wacc": 0.09,
        "typical_exit_multiple": 14.0,
        "median_ev_ebitda": 11.0,
        "median_ev_revenue": 1.5
    },
    "Real Estate": {
        "typical_ebitda_margin": 0.60,
        "typical_revenue_growth": 0.03,
        "typical_wacc": 0.08,
        "typical_exit_multiple": 20.0,
        "median_ev_ebitda": 22.0,
        "median_ev_revenue": 8.0
    }
}

MOCK_TRANSACTIONS = {
    "Technology": [
        {"company": "TechCorp A", "transaction_date": "2024-06", "deal_value_usd_m": 1200, "revenue_usd_m": 180, "ebitda_usd_m": 45, "ev_revenue": 6.7, "ev_ebitda": 26.7, "p_e": 32.0},
        {"company": "CloudSys B", "transaction_date": "2024-04", "deal_value_usd_m": 850, "revenue_usd_m": 120, "ebitda_usd_m": 30, "ev_revenue": 7.1, "ev_ebitda": 28.3, "p_e": 35.0},
        {"company": "DataFlow C", "transaction_date": "2024-02", "deal_value_usd_m": 650, "revenue_usd_m": 95, "ebitda_usd_m": 24, "ev_revenue": 6.8, "ev_ebitda": 27.1, "p_e": 33.0},
        {"company": "AIStartup D", "transaction_date": "2023-11", "deal_value_usd_m": 450, "revenue_usd_m": 60, "ebitda_usd_m": 15, "ev_revenue": 7.5, "ev_ebitda": 30.0, "p_e": 38.0},
        {"company": "SaaSPlatform E", "transaction_date": "2023-09", "deal_value_usd_m": 1100, "revenue_usd_m": 165, "ebitda_usd_m": 41, "ev_revenue": 6.7, "ev_ebitda": 26.8, "p_e": 31.0},
        {"company": "CyberSec F", "transaction_date": "2023-07", "deal_value_usd_m": 720, "revenue_usd_m": 108, "ebitda_usd_m": 27, "ev_revenue": 6.7, "ev_ebitda": 26.7, "p_e": 34.0},
    ],
    "Healthcare": [
        {"company": "BioMed A", "transaction_date": "2024-05", "deal_value_usd_m": 950, "revenue_usd_m": 210, "ebitda_usd_m": 42, "ev_revenue": 4.5, "ev_ebitda": 22.6, "p_e": 28.0},
        {"company": "HealthTech B", "transaction_date": "2024-03", "deal_value_usd_m": 680, "revenue_usd_m": 155, "ebitda_usd_m": 31, "ev_revenue": 4.4, "ev_ebitda": 21.9, "p_e": 26.0},
        {"company": "PharmaServ C", "transaction_date": "2023-12", "deal_value_usd_m": 520, "revenue_usd_m": 120, "ebitda_usd_m": 24, "ev_revenue": 4.3, "ev_ebitda": 21.7, "p_e": 25.0},
        {"company": "MedDevice D", "transaction_date": "2023-10", "deal_value_usd_m": 780, "revenue_usd_m": 175, "ebitda_usd_m": 35, "ev_revenue": 4.5, "ev_ebitda": 22.3, "p_e": 27.0},
    ],
    "Energy": [
        {"company": "GreenPower A", "transaction_date": "2024-04", "deal_value_usd_m": 2200, "revenue_usd_m": 440, "ebitda_usd_m": 154, "ev_revenue": 5.0, "ev_ebitda": 14.3, "p_e": 18.0},
        {"company": "OilField B", "transaction_date": "2024-01", "deal_value_usd_m": 1800, "revenue_usd_m": 360, "ebitda_usd_m": 126, "ev_revenue": 5.0, "ev_ebitda": 14.3, "p_e": 17.0},
        {"company": "GasUtility C", "transaction_date": "2023-08", "deal_value_usd_m": 1400, "revenue_usd_m": 280, "ebitda_usd_m": 98, "ev_revenue": 5.0, "ev_ebitda": 14.3, "p_e": 16.0},
    ],
    "Financials": [
        {"company": "FinServ A", "transaction_date": "2024-06", "deal_value_usd_m": 1800, "revenue_usd_m": 360, "ebitda_usd_m": 162, "ev_revenue": 5.0, "ev_ebitda": 11.1, "p_e": 14.0},
        {"company": "PayTech B", "transaction_date": "2024-03", "deal_value_usd_m": 1200, "revenue_usd_m": 240, "ebitda_usd_m": 108, "ev_revenue": 5.0, "ev_ebitda": 11.1, "p_e": 15.0},
        {"company": "InsurTech C", "transaction_date": "2023-11", "deal_value_usd_m": 850, "revenue_usd_m": 170, "ebitda_usd_m": 77, "ev_revenue": 5.0, "ev_ebitda": 11.0, "p_e": 13.0},
    ],
    "Industrials": [
        {"company": "Manufacturing A", "transaction_date": "2024-05", "deal_value_usd_m": 850, "revenue_usd_m": 472, "ebitda_usd_m": 71, "ev_revenue": 1.8, "ev_ebitda": 12.0, "p_e": 15.0},
        {"company": "AutoParts B", "transaction_date": "2024-02", "deal_value_usd_m": 620, "revenue_usd_m": 344, "ebitda_usd_m": 52, "ev_revenue": 1.8, "ev_ebitda": 11.9, "p_e": 14.0},
        {"company": "Logistics C", "transaction_date": "2023-09", "deal_value_usd_m": 480, "revenue_usd_m": 267, "ebitda_usd_m": 40, "ev_revenue": 1.8, "ev_ebitda": 12.0, "p_e": 14.0},
    ],
    "Consumer": [
        {"company": "Retail A", "transaction_date": "2024-04", "deal_value_usd_m": 650, "revenue_usd_m": 433, "ebitda_usd_m": 52, "ev_revenue": 1.5, "ev_ebitda": 12.5, "p_e": 16.0},
        {"company": "FoodBrand B", "transaction_date": "2024-01", "deal_value_usd_m": 520, "revenue_usd_m": 347, "ebitda_usd_m": 42, "ev_revenue": 1.5, "ev_ebitda": 12.4, "p_e": 15.0},
        {"company": "Fashion C", "transaction_date": "2023-10", "deal_value_usd_m": 380, "revenue_usd_m": 253, "ebitda_usd_m": 30, "ev_revenue": 1.5, "ev_ebitda": 12.7, "p_e": 17.0},
    ],
    "Real Estate": [
        {"company": "REIT A", "transaction_date": "2024-06", "deal_value_usd_m": 3200, "revenue_usd_m": 400, "ebitda_usd_m": 240, "ev_revenue": 8.0, "ev_ebitda": 13.3, "p_e": 22.0},
        {"company": "PropDev B", "transaction_date": "2024-03", "deal_value_usd_m": 2400, "revenue_usd_m": 300, "ebitda_usd_m": 180, "ev_revenue": 8.0, "ev_ebitda": 13.3, "p_e": 21.0},
        {"company": "LogisticsRE C", "transaction_date": "2023-12", "deal_value_usd_m": 1800, "revenue_usd_m": 225, "ebitda_usd_m": 135, "ev_revenue": 8.0, "ev_ebitda": 13.3, "p_e": 20.0},
    ]
}

MOCK_NEWS_TEMPLATES = [
    {"source": "Reuters", "sentiment": "positive"},
    {"source": "Bloomberg", "sentiment": "neutral"},
    {"source": "Financial Times", "sentiment": "neutral"},
    {"source": "Wall Street Journal", "sentiment": "positive"},
    {"source": "CNBC", "sentiment": "negative"},
    {"source": "MarketWatch", "sentiment": "neutral"},
    {"source": "Forbes", "sentiment": "positive"},
    {"source": "TechCrunch", "sentiment": "positive"},
    {"source": "Business Insider", "sentiment": "neutral"},
    {"source": "The Economist", "sentiment": "negative"},
]


# ============================================================================
# Core M&A Tools
# ============================================================================

@tool
def get_sector_benchmarks(sector: str) -> Dict[str, Any]:
    """Returns typical financial benchmarks for a given sector."""
    return SECTOR_BENCHMARKS.get(sector, SECTOR_BENCHMARKS["Technology"])


@tool
def get_recent_transactions(sector: str, deal_type: str) -> List[Dict[str, Any]]:
    """Returns recent M&A transaction data for a sector."""
    return MOCK_TRANSACTIONS.get(sector, MOCK_TRANSACTIONS["Technology"])


@tool
def search_company_news(company_name: str, days_back: int) -> List[Dict[str, Any]]:
    """Searches for recent news about a company."""
    import random
    from datetime import datetime, timedelta
    
    news_items = []
    for i in range(10):
        template = MOCK_NEWS_TEMPLATES[i % len(MOCK_NEWS_TEMPLATES)]
        days_ago = random.randint(1, min(days_back, 90))
        published = datetime.now() - timedelta(days=days_ago)
        
        news_items.append({
            "headline": f"{company_name} {random.choice(['announces expansion', 'reports earnings', 'explores strategic options', 'partners with industry leader', 'launches new product line'])}",
            "source": template["source"],
            "published_at": published.isoformat(),
            "url": f"https://example.com/news/{i}",
            "summary": f"Recent development regarding {company_name} and its market position.",
            "sentiment": template["sentiment"],
            "relevance_tags": random.sample(["M&A", "Earnings", "Strategy", "Market Update"], k=2)
        })
    
    return news_items


@tool
def calculate_wacc(
    equity_beta: float,
    risk_free_rate: float,
    equity_risk_premium: float,
    debt_spread: float,
    tax_rate: float,
    debt_to_equity: float
) -> float:
    """Calculates WACC given capital structure inputs."""
    cost_of_equity = risk_free_rate + (equity_beta * equity_risk_premium)
    cost_of_debt = risk_free_rate + debt_spread
    
    debt_ratio = debt_to_equity / (1 + debt_to_equity)
    equity_ratio = 1 / (1 + debt_to_equity)
    
    wacc = (equity_ratio * cost_of_equity) + (debt_ratio * cost_of_debt * (1 - tax_rate))
    return round(wacc, 4)


# ============================================================================
# MCP-Backed Tools
# ============================================================================

def get_mcp_tools_for_agent(agent_type: str) -> List[Any]:
    """
    Get available MCP tools for a specific agent type.
    
    Args:
        agent_type: Type of agent (comps, dcf, news, document, pitchbook)
        
    Returns:
        List of available MCP tools for the agent
    """
    tool_mapping = {
        "comps": ["financial_data", "sec_edgar"],
        "dcf": ["financial_data"],
        "news": ["news"],
        "document": ["sec_edgar"],
        "pitchbook": ["financial_data", "sec_edgar", "news"]
    }
    
    server_types = tool_mapping.get(agent_type, [])
    if server_types:
        return mcp_registry.get_tools(server_types)
    return []


@tool
def search_sec_filings(company: str, form_type: str = "10-K", date_from: Optional[str] = None) -> Dict[str, Any]:
    """
    Search SEC filings for a company. MCP-backed tool.
    
    Args:
        company: Company name or ticker symbol
        form_type: SEC form type (10-K, 10-Q, 8-K, etc.)
        date_from: Start date in YYYY-MM-DD format (optional)
        
    Returns:
        Dictionary with filing results
    """
    tools = mcp_registry.get_tools(["sec_edgar"])
    if tools:
        # Use the first available SEC EDGAR tool
        for tool in tools:
            if "search_filings" in tool.name:
                try:
                    return tool.func(company=company, form_type=form_type, date_from=date_from)
                except Exception as e:
                    return {"success": False, "error": str(e), "filings": []}
    
    # Fallback: return empty result with MCP unavailable message
    return {
        "success": False,
        "error": "SEC EDGAR MCP server not connected",
        "filings": [],
        "note": "Connect SEC EDGAR MCP server in Settings to enable this feature"
    }


@tool
def get_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Get stock price and financial data for a company. MCP-backed tool.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
    Returns:
        Dictionary with stock data including price, ratios, etc.
    """
    tools = mcp_registry.get_tools(["financial_data"])
    if tools:
        for tool in tools:
            if "get_stock_price" in tool.name:
                try:
                    return tool.func(ticker=ticker)
                except Exception as e:
                    return {"success": False, "error": str(e)}
    
    return {
        "success": False,
        "error": "Financial data MCP server not connected",
        "note": "Connect Financial Data MCP server in Settings to enable this feature"
    }


@tool
def get_financial_ratios(ticker: str) -> Dict[str, Any]:
    """
    Get financial valuation ratios (P/E, EV/EBITDA, etc.). MCP-backed tool.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with financial ratios
    """
    tools = mcp_registry.get_tools(["financial_data"])
    if tools:
        for tool in tools:
            if "get_financial_ratios" in tool.name:
                try:
                    return tool.func(ticker=ticker)
                except Exception as e:
                    return {"success": False, "error": str(e)}
    
    return {
        "success": False,
        "error": "Financial data MCP server not connected",
        "note": "Connect Financial Data MCP server in Settings to enable this feature"
    }


@tool
def post_to_slack(channel: str, message: str) -> Dict[str, Any]:
    """
    Post a message to a Slack channel. MCP-backed tool.
    
    Args:
        channel: Channel name or ID (e.g., '#deals', 'C1234567890')
        message: Message text to post
        
    Returns:
        Dictionary with success status
    """
    tools = mcp_registry.get_tools(["slack"])
    if tools:
        for tool in tools:
            if "post_message" in tool.name:
                try:
                    return tool.func(channel=channel, text=message)
                except Exception as e:
                    return {"success": False, "error": str(e)}
    
    return {
        "success": False,
        "error": "Slack MCP server not connected",
        "note": "Connect Slack MCP server in Settings to enable this feature"
    }


@tool
def search_news_mcp(query: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for news articles using MCP news service. MCP-backed tool.
    
    Args:
        query: Search query string
        from_date: Start date in YYYY-MM-DD format (optional)
        to_date: End date in YYYY-MM-DD format (optional)
        
    Returns:
        Dictionary with news articles
    """
    tools = mcp_registry.get_tools(["news"])
    if tools:
        for tool in tools:
            if "search_news" in tool.name:
                try:
                    return tool.func(query=query, from_date=from_date, to_date=to_date)
                except Exception as e:
                    return {"success": False, "error": str(e), "articles": []}
    
    return {
        "success": False,
        "error": "News MCP server not connected",
        "articles": [],
        "note": "Connect News MCP server in Settings to enable this feature"
    }


# ============================================================================
# Tool List Exports
# ============================================================================

def get_all_mcp_tools() -> List[Any]:
    """Get all available MCP tools from connected servers."""
    return mcp_registry.get_tools()


def get_agent_toolset(agent_type: str) -> List[Any]:
    """
    Get the complete toolset for an agent including core and MCP tools.
    
    Args:
        agent_type: Type of agent
        
    Returns:
        Combined list of core tools and MCP tools
    """
    core_tools = [
        get_sector_benchmarks,
        get_recent_transactions,
        search_company_news,
        calculate_wacc
    ]
    
    mcp_tools = get_mcp_tools_for_agent(agent_type)
    
    return core_tools + mcp_tools
