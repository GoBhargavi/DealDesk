"""Pydantic schemas for Contact entities."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    """Base contact schema with common fields."""
    name: str
    title: str
    company: str
    email: str
    phone: Optional[str] = None
    is_counterparty: bool = False


class ContactCreate(ContactBase):
    """Schema for creating a new contact."""
    pass


class ContactUpdate(BaseModel):
    """Schema for updating contact fields."""
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_counterparty: Optional[bool] = None


class ContactInDBBase(ContactBase):
    """Base schema for contacts stored in database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    deal_id: UUID
    created_at: datetime


class Contact(ContactInDBBase):
    """Complete contact schema returned from API."""
    pass


class ContactList(BaseModel):
    """Schema for list of contacts."""
    contacts: list[Contact]
    total: int
