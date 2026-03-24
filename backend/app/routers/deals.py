"""Deals router for pipeline management endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.deal import Deal, DealCreate, DealUpdate, DealStageUpdate, DealList
from app.schemas.contact import Contact, ContactCreate, ContactList
from app.services.deal_service import DealService
from app.models.contact import Contact as ContactModel

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=DealList)
async def list_deals(
    stage: Optional[str] = Query(None, description="Filter by deal stage"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    deal_type: Optional[str] = Query(None, description="Filter by deal type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db)
) -> DealList:
    """
    List all deals with optional filtering.
    
    Query Parameters:
    - **stage**: Filter by deal stage (e.g., "Diligence", "LOI")
    - **sector**: Filter by industry sector
    - **deal_type**: Filter by transaction type (M&A, LBO, etc.)
    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return
    
    Returns a list of deals matching the filter criteria.
    """
    deals = await DealService.get_deals(db, stage, sector, deal_type, skip, limit)
    return DealList(deals=deals, total=len(deals))


@router.post("", response_model=Deal, status_code=status.HTTP_201_CREATED)
async def create_deal(
    deal_data: DealCreate,
    db: AsyncSession = Depends(get_db)
) -> Deal:
    """
    Create a new deal.
    
    The deal will be created in the "Origination" stage by default.
    A WebSocket event will be broadcast to all connected clients.
    
    Request Body:
    - **name**: Project name (e.g., "Project Falcon")
    - **target_company**: Target company name
    - **acquirer_company**: Acquirer/PE firm name
    - **deal_type**: Transaction type (M&A, LBO, IPO, Restructuring, Equity Raise)
    - **sector**: Industry sector
    - **region**: Geographic region
    - **lead_banker**: Lead investment banker name
    - Optional fields: deal_value_usd, expected_close_date, notes, assigned_team
    
    Returns the created deal with generated ID and timestamps.
    """
    deal = await DealService.create_deal(db, deal_data)
    return deal


@router.get("/{deal_id}", response_model=Deal)
async def get_deal(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Deal:
    """
    Get a specific deal by ID.
    
    Path Parameters:
    - **deal_id**: UUID of the deal to retrieve
    
    Returns the complete deal details including related contacts and documents.
    Raises 404 if deal not found.
    """
    deal = await DealService.get_deal_by_id(db, deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {deal_id} not found"
        )
    return deal


@router.patch("/{deal_id}", response_model=Deal)
async def update_deal(
    deal_id: UUID,
    deal_data: DealUpdate,
    db: AsyncSession = Depends(get_db)
) -> Deal:
    """
    Update deal fields.
    
    Only provided fields will be updated. Null or omitted fields are ignored.
    A WebSocket event will be broadcast for the update.
    
    Path Parameters:
    - **deal_id**: UUID of the deal to update
    
    Request Body:
    - Any subset of deal fields to update
    
    Returns the updated deal.
    Raises 404 if deal not found.
    """
    deal = await DealService.update_deal(db, deal_id, deal_data)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {deal_id} not found"
        )
    return deal


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a deal.
    
    This will also delete all associated contacts and documents.
    
    Path Parameters:
    - **deal_id**: UUID of the deal to delete
    
    Raises 404 if deal not found.
    """
    deleted = await DealService.delete_deal(db, deal_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {deal_id} not found"
        )


@router.patch("/{deal_id}/stage", response_model=Deal)
async def move_deal_stage(
    deal_id: UUID,
    stage_update: DealStageUpdate,
    db: AsyncSession = Depends(get_db)
) -> Deal:
    """
    Move a deal to a new stage.
    
    This triggers a WebSocket broadcast event notifying all clients
    of the stage change with animation support.
    
    Path Parameters:
    - **deal_id**: UUID of the deal to move
    
    Request Body:
    - **stage**: New stage value
    
    Valid stages: Origination, NDA Signed, Diligence, IOI, LOI, 
    Exclusivity, Signing, Closing, Closed, Dead
    
    Returns the updated deal.
    """
    deal = await DealService.update_deal_stage(db, deal_id, stage_update.stage)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {deal_id} not found"
        )
    return deal


@router.get("/{deal_id}/contacts", response_model=ContactList)
async def list_deal_contacts(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ContactList:
    """
    List all contacts for a deal.
    
    Path Parameters:
    - **deal_id**: UUID of the deal
    
    Returns a list of contacts associated with the deal.
    """
    contacts = await DealService.get_deal_contacts(db, deal_id)
    return ContactList(contacts=contacts, total=len(contacts))


@router.post("/{deal_id}/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def add_deal_contact(
    deal_id: UUID,
    contact_data: ContactCreate,
    db: AsyncSession = Depends(get_db)
) -> Contact:
    """
    Add a contact to a deal.
    
    Path Parameters:
    - **deal_id**: UUID of the deal
    
    Request Body:
    - **name**: Contact full name
    - **title**: Job title
    - **company**: Company name
    - **email**: Email address
    - **phone**: Optional phone number
    - **is_counterparty**: Whether this is a counterparty contact
    
    Returns the created contact.
    Raises 404 if deal not found.
    """
    deal = await DealService.get_deal_by_id(db, deal_id)
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID {deal_id} not found"
        )
    
    contact = ContactModel(
        deal_id=deal_id,
        **contact_data.model_dump()
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    
    return contact
