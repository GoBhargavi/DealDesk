"""Pydantic schemas for Deal entities."""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DealBase(BaseModel):
    """Base deal schema with common fields."""
    name: str
    target_company: str
    acquirer_company: str
    deal_type: str
    stage: str = "Origination"
    deal_value_usd: Optional[float] = None
    sector: str
    region: str
    expected_close_date: Optional[date] = None
    lead_banker: str
    assigned_team: List[str] = []
    notes: Optional[str] = None


class DealCreate(DealBase):
    """Schema for creating a new deal."""
    pass


class DealUpdate(BaseModel):
    """Schema for updating deal fields."""
    name: Optional[str] = None
    target_company: Optional[str] = None
    acquirer_company: Optional[str] = None
    deal_type: Optional[str] = None
    stage: Optional[str] = None
    deal_value_usd: Optional[float] = None
    sector: Optional[str] = None
    region: Optional[str] = None
    expected_close_date: Optional[date] = None
    lead_banker: Optional[str] = None
    assigned_team: Optional[List[str]] = None
    notes: Optional[str] = None


class DealStageUpdate(BaseModel):
    """Schema for updating deal stage."""
    stage: str


class DealInDBBase(DealBase):
    """Base schema for deals stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime


class Deal(DealInDBBase):
    """Complete deal schema returned from API."""
    pass


class DealList(BaseModel):
    """Schema for list of deals."""
    deals: List[Deal]
    total: int
