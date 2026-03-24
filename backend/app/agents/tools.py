"""LangChain tools for M&A agents."""

from typing import Dict, List, Any
from langchain.tools import tool


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
        "typical_exit_multiple": 11.0,
        "median_ev_ebitda": 10.5,
        "median_ev_revenue": 1.5
    },
    "Fintech": {
        "typical_ebitda_margin": 0.30,
        "typical_revenue_growth": 0.20,
        "typical_wacc": 0.12,
        "typical_exit_multiple": 20.0,
        "median_ev_ebitda": 25.0,
        "median_ev_revenue": 8.0
    }
}


MOCK_TRANSACTIONS = {
    "Technology": [
        {"company": "CloudSys Inc", "date": "2024-01", "value": 850, "revenue": 120, "ebitda": 28, "ev_revenue": 7.1, "ev_ebitda": 30.4, "pe": 42.0},
        {"company": "DataTech Corp", "date": "2024-02", "value": 2100, "revenue": 310, "ebitda": 78, "ev_revenue": 6.8, "ev_ebitda": 26.9, "pe": 38.5},
        {"company": "SoftStream", "date": "2023-11", "value": 450, "revenue": 72, "ebitda": 16, "ev_revenue": 6.3, "ev_ebitda": 28.1, "pe": 35.2},
        {"company": "CodeBase Solutions", "date": "2023-09", "value": 1800, "revenue": 280, "ebitda": 70, "ev_revenue": 6.4, "ev_ebitda": 25.7, "pe": 40.1},
    ],
    "Healthcare": [
        {"company": "MedDevice Pro", "date": "2024-01", "value": 620, "revenue": 95, "ebitda": 21, "ev_revenue": 6.5, "ev_ebitda": 29.5, "pe": 36.0},
        {"company": "BioHealth Systems", "date": "2023-12", "value": 1200, "revenue": 185, "ebitda": 38, "ev_revenue": 6.5, "ev_ebitda": 31.6, "pe": 38.2},
        {"company": "DiagnoTech", "date": "2023-08", "value": 380, "revenue": 58, "ebitda": 12, "ev_revenue": 6.6, "ev_ebitda": 31.7, "pe": 34.8},
    ],
    "Energy": [
        {"company": "GreenPower Co", "date": "2024-02", "value": 1500, "revenue": 320, "ebitda": 115, "ev_revenue": 4.7, "ev_ebitda": 13.0, "pe": 18.5},
        {"company": "SolarGen Inc", "date": "2023-10", "value": 920, "revenue": 180, "ebitda": 62, "ev_revenue": 5.1, "ev_ebitda": 14.8, "pe": 20.2},
    ],
    "Financials": [
        {"company": "PayFin Solutions", "date": "2023-11", "value": 780, "revenue": 145, "ebitda": 68, "ev_revenue": 5.4, "ev_ebitda": 11.5, "pe": 16.8},
        {"company": "InsurTech Corp", "date": "2024-01", "value": 1100, "revenue": 210, "ebitda": 95, "ev_revenue": 5.2, "ev_ebitda": 11.6, "pe": 15.5},
    ],
    "Industrials": [
        {"company": "LogiFlow Inc", "date": "2023-09", "value": 340, "revenue": 85, "ebitda": 13, "ev_revenue": 4.0, "ev_ebitda": 26.2, "pe": 28.0},
        {"company": "Manufacturing Pro", "date": "2023-12", "value": 890, "revenue": 195, "ebitda": 28, "ev_revenue": 4.6, "ev_ebitda": 31.8, "pe": 32.5},
    ],
    "Consumer": [
        {"company": "RetailMax", "date": "2023-10", "value": 560, "revenue": 180, "ebitda": 20, "ev_revenue": 3.1, "ev_ebitda": 28.0, "pe": 22.0},
        {"company": "Consumer Goods Co", "date": "2024-02", "value": 720, "revenue": 210, "ebitda": 26, "ev_revenue": 3.4, "ev_ebitda": 27.7, "pe": 24.5},
    ],
    "Fintech": [
        {"company": "FinStream Tech", "date": "2024-01", "value": 950, "revenue": 120, "ebitda": 38, "ev_revenue": 7.9, "ev_ebitda": 25.0, "pe": 38.0},
        {"company": "PaymentHub", "date": "2023-12", "value": 1400, "revenue": 180, "ebitda": 58, "ev_revenue": 7.8, "ev_ebitda": 24.1, "pe": 36.5},
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
