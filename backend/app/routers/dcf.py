"""DCF router for financial modeling endpoints."""

import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.orchestrator import run_agent_task

router = APIRouter(prefix="/dcf", tags=["dcf"])


class DCFInputs(BaseModel):
    """DCF model input parameters."""
    deal_id: str
    company_name: str
    projection_years: int = 5
    revenue_base: float
    revenue_growth_rates: List[float]
    ebitda_margins: List[float]
    capex_pct_revenue: float
    nwc_change_pct_revenue: float
    tax_rate: float
    wacc: float
    terminal_growth_rate: float
    exit_multiple: float
    net_debt: float
    shares_outstanding: Optional[float] = None


class DCFYearlyResult(BaseModel):
    """Yearly DCF calculation result."""
    year: int
    revenue: float
    ebitda: float
    ebit: float
    taxes: float
    nopat: float
    depreciation: float
    capex: float
    nwc_change: float
    fcf: float
    pv_factor: float
    pv_fcf: float


class DCFResult(BaseModel):
    """Complete DCF calculation result."""
    deal_id: str
    company_name: str
    yearly_results: List[DCFYearlyResult]
    sum_pv_fcf: float
    terminal_value: float
    pv_terminal_value: float
    enterprise_value: float
    net_debt: float
    equity_value: float
    implied_share_price: Optional[float]
    sensitivity_table: List[List[float]]


class DCFAIAssistRequest(BaseModel):
    """Request for AI-assisted DCF assumptions."""
    deal_id: str
    company_description: str
    sector: str
    recent_financials_text: Optional[str] = None


def calculate_dcf(inputs: DCFInputs) -> DCFResult:
    """
    Calculate DCF valuation based on inputs.
    
    Args:
        inputs: DCF model parameters
        
    Returns:
        Complete DCF calculation result
    """
    yearly_results = []
    revenue = inputs.revenue_base
    
    for year in range(1, inputs.projection_years + 1):
        growth_rate = inputs.revenue_growth_rates[year - 1]
        ebitda_margin = inputs.ebitda_margins[year - 1]
        
        revenue = revenue * (1 + growth_rate)
        ebitda = revenue * ebitda_margin
        
        # Assume D&A is 20% of EBITDA for simplicity
        depreciation = ebitda * 0.20
        ebit = ebitda - depreciation
        
        taxes = max(0, ebit * inputs.tax_rate)
        nopat = ebit - taxes
        
        capex = revenue * inputs.capex_pct_revenue
        nwc_change = revenue * inputs.nwc_change_pct_revenue
        
        fcf = nopat + depreciation - capex - nwc_change
        
        pv_factor = 1 / ((1 + inputs.wacc) ** year)
        pv_fcf = fcf * pv_factor
        
        yearly_results.append(DCFYearlyResult(
            year=year,
            revenue=round(revenue, 2),
            ebitda=round(ebitda, 2),
            ebit=round(ebit, 2),
            taxes=round(taxes, 2),
            nopat=round(nopat, 2),
            depreciation=round(depreciation, 2),
            capex=round(capex, 2),
            nwc_change=round(nwc_change, 2),
            fcf=round(fcf, 2),
            pv_factor=round(pv_factor, 4),
            pv_fcf=round(pv_fcf, 2)
        ))
    
    sum_pv_fcf = sum(r.pv_fcf for r in yearly_results)
    
    # Terminal value calculation
    final_ebitda = yearly_results[-1].ebitda
    terminal_value = final_ebitda * inputs.exit_multiple
    pv_terminal_value = terminal_value / ((1 + inputs.wacc) ** inputs.projection_years)
    
    enterprise_value = sum_pv_fcf + pv_terminal_value
    equity_value = enterprise_value - inputs.net_debt
    
    implied_share_price = None
    if inputs.shares_outstanding and inputs.shares_outstanding > 0:
        implied_share_price = equity_value / inputs.shares_outstanding
    
    # Sensitivity table (WACC x Exit Multiple)
    wacc_range = [inputs.wacc - 0.02, inputs.wacc - 0.01, inputs.wacc, 
                  inputs.wacc + 0.01, inputs.wacc + 0.02]
    multiple_range = [inputs.exit_multiple - 2, inputs.exit_multiple - 1, inputs.exit_multiple,
                      inputs.exit_multiple + 1, inputs.exit_multiple + 2]
    
    sensitivity_table = []
    for w in wacc_range:
        row = []
        for m in multiple_range:
            tv = final_ebitda * m
            pv_tv = tv / ((1 + w) ** inputs.projection_years)
            
            # Recalculate PV of FCFs with new WACC
            sum_pv = 0
            for year, yr in enumerate(yearly_results):
                pv_f = yr.fcf / ((1 + w) ** (year + 1))
                sum_pv += pv_f
            
            ev = sum_pv + pv_tv
            row.append(round(ev, 1))
        sensitivity_table.append(row)
    
    return DCFResult(
        deal_id=inputs.deal_id,
        company_name=inputs.company_name,
        yearly_results=yearly_results,
        sum_pv_fcf=round(sum_pv_fcf, 2),
        terminal_value=round(terminal_value, 2),
        pv_terminal_value=round(pv_terminal_value, 2),
        enterprise_value=round(enterprise_value, 2),
        net_debt=round(inputs.net_debt, 2),
        equity_value=round(equity_value, 2),
        implied_share_price=round(implied_share_price, 2) if implied_share_price else None,
        sensitivity_table=sensitivity_table
    )


@router.post("/calculate", response_model=DCFResult)
async def calculate_dcf_endpoint(inputs: DCFInputs) -> DCFResult:
    """
    Calculate DCF valuation synchronously.
    
    This endpoint performs a pure calculation without AI assistance.
    All parameters must be provided in the request body.
    
    Request Body:
    - **deal_id**: Deal identifier
    - **company_name**: Company being valued
    - **revenue_base**: Base revenue in $M
    - **revenue_growth_rates**: List of 5 annual growth rates
    - **ebitda_margins**: List of 5 EBITDA margins
    - **capex_pct_revenue**: CapEx as % of revenue
    - **nwc_change_pct_revenue**: NWC change as % of revenue
    - **tax_rate**: Corporate tax rate
    - **wacc**: Weighted average cost of capital
    - **terminal_growth_rate**: Terminal growth rate
    - **exit_multiple**: Terminal exit multiple
    - **net_debt**: Net debt in $M
    - **shares_outstanding**: Shares outstanding (optional, for per-share value)
    
    Returns complete DCF result including:
    - Year-by-year projections
    - Enterprise and equity values
    - Implied share price
    - Sensitivity table (WACC vs Exit Multiple)
    """
    return calculate_dcf(inputs)


@router.post("/ai-assist")
async def ai_assist_dcf(request: DCFAIAssistRequest) -> StreamingResponse:
    """
    Get AI-suggested DCF assumptions via SSE.
    
    The DCFAgent analyzes the company description and sector to suggest
    realistic financial projections and valuation parameters.
    
    Request Body:
    - **deal_id**: Deal identifier
    - **company_description**: Description of the target company
    - **sector**: Industry sector
    - **recent_financials_text**: Optional recent financial data
    
    SSE Events:
    - `reasoning`: Agent analysis steps
    - `assumptions`: Suggested DCF parameters
    - `done`: Stream completion
    """
    
    async def event_generator():
        try:
            reasoning_steps = []
            
            def streaming_callback(step: str):
                reasoning_steps.append(step)
            
            yield f"event: reasoning\ndata: {json.dumps({'step': 'Analyzing company profile and sector benchmarks...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Run the DCF agent for assumptions
            result = await run_agent_task(
                task_type="dcf",
                deal_id=request.deal_id,
                input_data={
                    "company_description": request.company_description,
                    "sector": request.sector,
                    "recent_financials_text": request.recent_financials_text
                },
                streaming_callback=streaming_callback
            )
            
            # Yield assumptions
            yield f"event: assumptions\ndata: {json.dumps(result)}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
