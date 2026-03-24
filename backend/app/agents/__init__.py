"""Agents package for multi-agent orchestration."""

from app.agents.orchestrator import run_agent_task, get_orchestrator, AgentState
from app.agents.comps_agent import CompsAgent
from app.agents.dcf_agent import DCFAgent
from app.agents.news_agent import NewsAgent
from app.agents.document_agent import DocumentAgent
from app.agents.tools import (
    get_sector_benchmarks,
    get_recent_transactions,
    search_company_news,
    calculate_wacc
)

__all__ = [
    "run_agent_task",
    "get_orchestrator",
    "AgentState",
    "CompsAgent",
    "DCFAgent",
    "NewsAgent",
    "DocumentAgent",
    "get_sector_benchmarks",
    "get_recent_transactions",
    "search_company_news",
    "calculate_wacc"
]
