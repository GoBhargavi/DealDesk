"""Deal service for business logic operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deal import Deal
from app.models.contact import Contact
from app.schemas.deal import DealCreate, DealUpdate
from app.services.redis_service import publish_event


class DealService:
    """Service class for deal operations."""
    
    @staticmethod
    async def get_deals(
        db: AsyncSession,
        stage: Optional[str] = None,
        sector: Optional[str] = None,
        deal_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Deal]:
        """
        Get deals with optional filtering.
        
        Args:
            db: Database session
            stage: Filter by deal stage
            sector: Filter by sector
            deal_type: Filter by deal type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Deal objects
        """
        query = select(Deal)
        
        conditions = []
        if stage:
            conditions.append(Deal.stage == stage)
        if sector:
            conditions.append(Deal.sector == sector)
        if deal_type:
            conditions.append(Deal.deal_type == deal_type)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(Deal.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_deal_by_id(db: AsyncSession, deal_id: UUID) -> Optional[Deal]:
        """
        Get a single deal by ID.
        
        Args:
            db: Database session
            deal_id: Deal UUID
            
        Returns:
            Deal object or None if not found
        """
        result = await db.execute(select(Deal).where(Deal.id == deal_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_deal(db: AsyncSession, deal_data: DealCreate) -> Deal:
        """
        Create a new deal.
        
        Args:
            db: Database session
            deal_data: Deal creation data
            
        Returns:
            Created Deal object
        """
        deal = Deal(**deal_data.model_dump())
        db.add(deal)
        await db.flush()
        await db.refresh(deal)
        
        # Publish event
        await publish_event("dealdesk:events", {
            "event": "deal_created",
            "deal": {
                "id": str(deal.id),
                "name": deal.name,
                "stage": deal.stage,
                "target_company": deal.target_company,
                "sector": deal.sector
            }
        })
        
        return deal
    
    @staticmethod
    async def update_deal(
        db: AsyncSession,
        deal_id: UUID,
        deal_data: DealUpdate
    ) -> Optional[Deal]:
        """
        Update a deal.
        
        Args:
            db: Database session
            deal_id: Deal UUID
            deal_data: Deal update data
            
        Returns:
            Updated Deal object or None if not found
        """
        deal = await DealService.get_deal_by_id(db, deal_id)
        if not deal:
            return None
        
        update_data = deal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(deal, field, value)
        
        await db.flush()
        await db.refresh(deal)
        
        # Publish event
        await publish_event("dealdesk:events", {
            "event": "deal_updated",
            "deal_id": str(deal_id),
            "fields": list(update_data.keys())
        })
        
        return deal
    
    @staticmethod
    async def update_deal_stage(
        db: AsyncSession,
        deal_id: UUID,
        new_stage: str
    ) -> Optional[Deal]:
        """
        Update a deal's stage.
        
        Args:
            db: Database session
            deal_id: Deal UUID
            new_stage: New stage value
            
        Returns:
            Updated Deal object or None if not found
        """
        deal = await DealService.get_deal_by_id(db, deal_id)
        if not deal:
            return None
        
        old_stage = deal.stage
        deal.stage = new_stage
        
        await db.flush()
        await db.refresh(deal)
        
        # Publish event
        await publish_event("dealdesk:events", {
            "event": "deal_stage_changed",
            "deal_id": str(deal_id),
            "from_stage": old_stage,
            "to_stage": new_stage
        })
        
        return deal
    
    @staticmethod
    async def delete_deal(db: AsyncSession, deal_id: UUID) -> bool:
        """
        Delete a deal.
        
        Args:
            db: Database session
            deal_id: Deal UUID
            
        Returns:
            True if deleted, False if not found
        """
        deal = await DealService.get_deal_by_id(db, deal_id)
        if not deal:
            return False
        
        await db.delete(deal)
        await db.flush()
        
        return True
    
    @staticmethod
    async def get_deal_contacts(db: AsyncSession, deal_id: UUID) -> List[Contact]:
        """
        Get all contacts for a deal.
        
        Args:
            db: Database session
            deal_id: Deal UUID
            
        Returns:
            List of Contact objects
        """
        deal = await DealService.get_deal_by_id(db, deal_id)
        if not deal:
            return []
        return deal.contacts
    
    @staticmethod
    async def seed_deals_if_empty(db: AsyncSession) -> None:
        """
        Seed the database with initial deals if empty.
        
        Args:
            db: Database session
        """
        result = await db.execute(select(Deal).limit(1))
        if result.scalar_one_or_none():
            return
        
        seed_data = [
            {
                "name": "Project Falcon",
                "target_company": "NovaTech Solutions",
                "acquirer_company": "Apex Capital Partners",
                "deal_type": "M&A",
                "stage": "Diligence",
                "deal_value_usd": 1240,
                "sector": "Technology",
                "region": "North America",
                "lead_banker": "Sarah Chen",
                "assigned_team": ["Sarah Chen", "Mike Johnson", "Lisa Wong"]
            },
            {
                "name": "Project Atlas",
                "target_company": "MedCore Diagnostics",
                "acquirer_company": "HealthVenture PE",
                "deal_type": "LBO",
                "stage": "LOI",
                "deal_value_usd": 680,
                "sector": "Healthcare",
                "region": "North America",
                "lead_banker": "James Whitfield",
                "assigned_team": ["James Whitfield", "Anna Park"]
            },
            {
                "name": "Project Horizon",
                "target_company": "GreenShift Energy",
                "acquirer_company": "EuroCapital Group",
                "deal_type": "M&A",
                "stage": "NDA Signed",
                "deal_value_usd": 2100,
                "sector": "Energy",
                "region": "Europe",
                "lead_banker": "Sarah Chen",
                "assigned_team": ["Sarah Chen", "David Miller"]
            },
            {
                "name": "Project Mercury",
                "target_company": "LogiStream Inc",
                "acquirer_company": "Pacific Logistics Corp",
                "deal_type": "M&A",
                "stage": "Signing",
                "deal_value_usd": 450,
                "sector": "Industrials",
                "region": "Asia Pacific",
                "lead_banker": "David Park",
                "assigned_team": ["David Park", "Jennifer Lee"]
            },
            {
                "name": "Project Vantage",
                "target_company": "FinStream Analytics",
                "acquirer_company": "Meridian Asset Mgmt",
                "deal_type": "Equity Raise",
                "stage": "Origination",
                "deal_value_usd": 320,
                "sector": "Fintech",
                "region": "North America",
                "lead_banker": "Rachel Torres",
                "assigned_team": ["Rachel Torres", "Kevin Brown"]
            },
            {
                "name": "Project Crown",
                "target_company": "RetailMax Group",
                "acquirer_company": "Stonegate Capital",
                "deal_type": "Restructuring",
                "stage": "Exclusivity",
                "deal_value_usd": 890,
                "sector": "Consumer",
                "region": "North America",
                "lead_banker": "James Whitfield",
                "assigned_team": ["James Whitfield", "Tom Anderson"]
            },
            {
                "name": "Project Titan",
                "target_company": "CloudArch Systems",
                "acquirer_company": "TechGiant Corp",
                "deal_type": "M&A",
                "stage": "Closed",
                "deal_value_usd": 3400,
                "sector": "Technology",
                "region": "North America",
                "lead_banker": "David Park",
                "assigned_team": ["David Park", "Lisa Wong", "Mark Chen"]
            },
            {
                "name": "Project Nova",
                "target_company": "BioPharm Innovations",
                "acquirer_company": "GlobalPharma Ltd",
                "deal_type": "M&A",
                "stage": "IOI",
                "deal_value_usd": 1750,
                "sector": "Healthcare",
                "region": "Europe",
                "lead_banker": "Sarah Chen",
                "assigned_team": ["Sarah Chen", "James Whitfield"]
            }
        ]
        
        for data in seed_data:
            deal = Deal(**data)
            db.add(deal)
        
        await db.flush()
