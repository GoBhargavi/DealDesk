"""FastAPI main application entry point with Phase 2 extensions."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_all_tables, check_database_connection
from app.routers import (
    deals_router,
    comps_router,
    dcf_router,
    pitchbook_router,
    news_router,
    documents_router,
    ws_router,
    settings_router
)
from app.services.redis_service import get_redis_client, close_redis_connection
from app.services.deal_service import DealService
from app.services.llm_factory import llm_factory, encrypt_api_key
from app.services.mcp_registry import mcp_registry
from app.database import AsyncSessionLocal
from app.models.llm_config import LLMConfig, SearchConfig
from sqlalchemy import select

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print("🚀 Starting up DealDesk API...")
    
    # Create database tables
    await create_all_tables()
    print("✅ Database tables created")
    
    # Check database connection
    if await check_database_connection():
        print("✅ Database connection established")
    else:
        print("⚠️  Database connection failed")
    
    # Initialize Redis connection
    await get_redis_client()
    print("✅ Redis connection established")
    
    # Seed database with initial deals if empty
    async with AsyncSessionLocal() as session:
        await DealService.seed_deals_if_empty(session)
        await session.commit()
        print("✅ Database seeded with initial deals")
        
        # Initialize default LLM config if none exists
        result = await session.execute(select(LLMConfig).where(LLMConfig.is_active == True))
        existing_llm = result.scalar_one_or_none()
        
        if not existing_llm and settings.ANTHROPIC_API_KEY:
            default_llm = LLMConfig(
                provider="anthropic",
                model_id="claude-sonnet-4-20250514",
                api_key=encrypt_api_key(settings.ANTHROPIC_API_KEY),
                is_active=True
            )
            session.add(default_llm)
            await session.commit()
            print("✅ Default LLM configuration created")
        
        # Initialize default search config if none exists
        result = await session.execute(select(SearchConfig).where(SearchConfig.is_active == True))
        existing_search = result.scalar_one_or_none()
        
        if not existing_search:
            default_search = SearchConfig(
                provider="tavily",
                api_key=None,  # User must configure
                max_results_per_query=5,
                max_queries_per_task=5,
                enable_full_page_fetch=True,
                is_active=True
            )
            session.add(default_search)
            await session.commit()
            print("✅ Default search configuration created (API key required)")
        
        # Initialize MCP Registry
        await mcp_registry.initialise(session)
        print("✅ MCP Registry initialized")
    
    print("🎯 DealDesk API ready")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down DealDesk API...")
    await close_redis_connection()
    print("✅ Redis connection closed")


# Create FastAPI application
app = FastAPI(
    title="DealDesk API",
    description="Agentic M&A Intelligence Platform for Investment Bankers",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api/v1 prefix
app.include_router(deals_router, prefix="/api/v1")
app.include_router(comps_router, prefix="/api/v1")
app.include_router(dcf_router, prefix="/api/v1")
app.include_router(pitchbook_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")  # Phase 2: Settings router


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and connectivity information.
    """
    db_ok = await check_database_connection()
    
    try:
        redis = await get_redis_client()
        redis_ok = await redis.ping()
    except Exception:
        redis_ok = False
    
    status_code = "healthy" if db_ok and redis_ok else "degraded"
    
    return {
        "status": status_code,
        "version": "1.0.0",
        "services": {
            "database": "connected" if db_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected"
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DealDesk API",
        "version": "1.0.0",
        "description": "Agentic M&A Intelligence Platform for Investment Bankers",
        "docs": "/docs",
        "health": "/health"
    }
