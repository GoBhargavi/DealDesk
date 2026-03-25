"""
Settings Router for DealDesk Phase 2.

Provides endpoints for:
- LLM Provider configuration (BYOLLM)
- Search Provider configuration (Deep Search)
- MCP Server configuration
- Agent LLM overrides
- Research agent endpoint
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models.llm_config import LLMConfig, AgentLLMOverride, SearchConfig, MCPServerConfig
from app.schemas.settings import (
    LLMConfigCreate, LLMConfigResponse, LLMConfigUpdate, LLMProviderInfo,
    AgentLLMOverrideCreate, AgentLLMOverrideResponse, AgentOverrideUpdate,
    SearchConfigCreate, SearchConfigResponse, SearchConfigUpdate, SearchTestResult,
    MCPServerConfigCreate, MCPServerConfigResponse, MCPServerConfigUpdate, MCPServerStatus,
    SettingsSummary, ResearchRequest, ResearchResult, ValidationResult
)
from app.services.llm_factory import llm_factory, encrypt_api_key, decrypt_api_key, mask_api_key
from app.services.deep_search import deep_search_service
from app.services.mcp_registry import mcp_registry
from app.services.redis_service import redis_service
from app.config import settings
from app.agents.research_agent import run_research_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

# ============================================================================
# LLM Provider Endpoints
# ============================================================================

@router.get("/llm", response_model=Optional[LLMConfigResponse])
async def get_active_llm_config(db: AsyncSession = Depends(get_db)) -> Optional[LLMConfigResponse]:
    """Get the currently active LLM configuration (with masked API key)."""
    result = await db.execute(select(LLMConfig).where(LLMConfig.is_active == True))
    config = result.scalar_one_or_none()
    
    if not config:
        return None
    
    return LLMConfigResponse(
        id=config.id,
        provider=config.provider,
        model_id=config.model_id,
        api_key_masked=mask_api_key(decrypt_api_key(config.api_key)) if config.api_key else None,
        base_url=config.base_url,
        api_version=config.api_version,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/llm", response_model=LLMConfigResponse)
async def set_llm_config(
    config_data: LLMConfigCreate,
    db: AsyncSession = Depends(get_db)
) -> LLMConfigResponse:
    """
    Set the active LLM configuration.
    
    Validates the config by making a test API call before saving.
    Deactivates the current config and saves the new one.
    """
    # Validate the config first
    test_config = LLMConfig(
        provider=config_data.provider,
        model_id=config_data.model_id,
        api_key=encrypt_api_key(config_data.api_key) if config_data.api_key else None,
        base_url=config_data.base_url,
        api_version=config_data.api_version,
        is_active=True
    )
    
    valid, error_msg = await llm_factory.validate_config(test_config)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"LLM configuration validation failed: {error_msg}"
        )
    
    # Deactivate current config
    await db.execute(
        select(LLMConfig).where(LLMConfig.is_active == True)
    )
    current_result = await db.execute(select(LLMConfig).where(LLMConfig.is_active == True))
    current = current_result.scalar_one_or_none()
    if current:
        current.is_active = False
    
    # Create new config
    new_config = LLMConfig(
        provider=config_data.provider,
        model_id=config_data.model_id,
        api_key=encrypt_api_key(config_data.api_key) if config_data.api_key else None,
        base_url=config_data.base_url,
        api_version=config_data.api_version,
        is_active=True
    )
    
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    # Clear cache
    await llm_factory.invalidate_cache()
    
    logger.info(f"New LLM config activated: {new_config.provider}/{new_config.model_id}")
    
    return LLMConfigResponse(
        id=new_config.id,
        provider=new_config.provider,
        model_id=new_config.model_id,
        api_key_masked=mask_api_key(config_data.api_key),
        base_url=new_config.base_url,
        api_version=new_config.api_version,
        is_active=new_config.is_active,
        created_at=new_config.created_at,
        updated_at=new_config.updated_at
    )


@router.get("/llm/providers", response_model=List[LLMProviderInfo])
async def get_supported_llm_providers() -> List[LLMProviderInfo]:
    """Get list of supported LLM providers with their required fields and available models."""
    return [
        LLMProviderInfo(
            id="anthropic",
            label="Anthropic Claude",
            models=[
                "claude-opus-4-20250514",
                "claude-sonnet-4-20250514",
                "claude-haiku-4-5-20251001"
            ],
            required_fields=["api_key"],
            optional_fields=[]
        ),
        LLMProviderInfo(
            id="openai",
            label="OpenAI",
            models=[
                "gpt-4o",
                "gpt-4o-mini",
                "o3",
                "o4-mini"
            ],
            required_fields=["api_key"],
            optional_fields=[]
        ),
        LLMProviderInfo(
            id="google",
            label="Google Gemini",
            models=[
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-2.5-flash"
            ],
            required_fields=["api_key"],
            optional_fields=[]
        ),
        LLMProviderInfo(
            id="azure_openai",
            label="Azure OpenAI",
            models=[],  # Dynamic based on deployment
            required_fields=["api_key", "base_url", "model_id", "api_version"],
            optional_fields=[]
        ),
        LLMProviderInfo(
            id="ollama",
            label="Ollama (local)",
            models=[
                "llama3.3",
                "mistral",
                "deepseek-r1",
                "qwen2.5"
            ],
            required_fields=["base_url", "model_id"],
            optional_fields=[]
        )
    ]


@router.post("/llm/validate", response_model=ValidationResult)
async def validate_llm_config(config_data: LLMConfigCreate) -> ValidationResult:
    """Validate an LLM configuration without saving it."""
    test_config = LLMConfig(
        provider=config_data.provider,
        model_id=config_data.model_id,
        api_key=encrypt_api_key(config_data.api_key) if config_data.api_key else None,
        base_url=config_data.base_url,
        api_version=config_data.api_version,
        is_active=False
    )
    
    valid, error_msg = await llm_factory.validate_config(test_config)
    
    return ValidationResult(
        valid=valid,
        message="Configuration is valid" if valid else error_msg
    )


# ============================================================================
# Agent Override Endpoints
# ============================================================================

@router.get("/llm/overrides", response_model=List[AgentLLMOverrideResponse])
async def get_agent_overrides(db: AsyncSession = Depends(get_db)) -> List[AgentLLMOverrideResponse]:
    """Get all agent LLM overrides."""
    result = await db.execute(
        select(AgentLLMOverride)
        .join(LLMConfig)
        .where(AgentLLMOverride.is_active == True)
    )
    overrides = result.scalars().all()
    
    return [
        AgentLLMOverrideResponse(
            id=o.id,
            agent_name=o.agent_name,
            llm_config_id=o.llm_config_id,
            is_active=o.is_active,
            llm_config=LLMConfigResponse(
                id=o.llm_config.id,
                provider=o.llm_config.provider,
                model_id=o.llm_config.model_id,
                api_key_masked=mask_api_key(decrypt_api_key(o.llm_config.api_key)) if o.llm_config.api_key else None,
                base_url=o.llm_config.base_url,
                api_version=o.llm_config.api_version,
                is_active=o.llm_config.is_active,
                created_at=o.llm_config.created_at,
                updated_at=o.llm_config.updated_at
            ) if o.llm_config else None,
            created_at=o.created_at
        )
        for o in overrides
    ]


@router.put("/llm/overrides/{agent_name}", response_model=AgentLLMOverrideResponse)
async def set_agent_override(
    agent_name: str,
    override_data: AgentOverrideUpdate,
    db: AsyncSession = Depends(get_db)
) -> AgentLLMOverrideResponse:
    """Set or update an agent LLM override."""
    # Validate agent name
    valid_agents = ["comps", "dcf", "news", "document", "pitchbook", "research"]
    if agent_name not in valid_agents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent name. Must be one of: {', '.join(valid_agents)}"
        )
    
    # Check if override exists
    result = await db.execute(
        select(AgentLLMOverride).where(AgentLLMOverride.agent_name == agent_name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing
        if override_data.llm_config_id is not None:
            existing.llm_config_id = override_data.llm_config_id
        if override_data.is_active is not None:
            existing.is_active = override_data.is_active
    else:
        # Create new
        if not override_data.llm_config_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="llm_config_id is required to create new override"
            )
        
        existing = AgentLLMOverride(
            agent_name=agent_name,
            llm_config_id=override_data.llm_config_id,
            is_active=override_data.is_active if override_data.is_active is not None else True
        )
        db.add(existing)
    
    await db.commit()
    await db.refresh(existing)
    
    # Clear cache
    await redis_service.delete(f"llm_factory:agent:{agent_name}")
    
    return AgentLLMOverrideResponse(
        id=existing.id,
        agent_name=existing.agent_name,
        llm_config_id=existing.llm_config_id,
        is_active=existing.is_active,
        created_at=existing.created_at
    )


# ============================================================================
# Search Provider Endpoints
# ============================================================================

@router.get("/search", response_model=Optional[SearchConfigResponse])
async def get_search_config(db: AsyncSession = Depends(get_db)) -> Optional[SearchConfigResponse]:
    """Get the currently active search configuration."""
    result = await db.execute(select(SearchConfig).where(SearchConfig.is_active == True))
    config = result.scalar_one_or_none()
    
    if not config:
        return None
    
    return SearchConfigResponse(
        id=config.id,
        provider=config.provider,
        api_key_masked=mask_api_key(decrypt_api_key(config.api_key)) if config.api_key else None,
        max_results_per_query=config.max_results_per_query,
        max_queries_per_task=config.max_queries_per_task,
        enable_full_page_fetch=config.enable_full_page_fetch,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/search", response_model=SearchConfigResponse)
async def set_search_config(
    config_data: SearchConfigCreate,
    db: AsyncSession = Depends(get_db)
) -> SearchConfigResponse:
    """Set the active search configuration."""
    # Deactivate current config
    current_result = await db.execute(select(SearchConfig).where(SearchConfig.is_active == True))
    current = current_result.scalar_one_or_none()
    if current:
        current.is_active = False
    
    # Create new config
    new_config = SearchConfig(
        provider=config_data.provider,
        api_key=encrypt_api_key(config_data.api_key) if config_data.api_key else None,
        max_results_per_query=config_data.max_results_per_query,
        max_queries_per_task=config_data.max_queries_per_task,
        enable_full_page_fetch=config_data.enable_full_page_fetch,
        is_active=True
    )
    
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    logger.info(f"New search config activated: {new_config.provider}")
    
    return SearchConfigResponse(
        id=new_config.id,
        provider=new_config.provider,
        api_key_masked=mask_api_key(config_data.api_key),
        max_results_per_query=new_config.max_results_per_query,
        max_queries_per_task=new_config.max_queries_per_task,
        enable_full_page_fetch=new_config.enable_full_page_fetch,
        is_active=new_config.is_active,
        created_at=new_config.created_at,
        updated_at=new_config.updated_at
    )


@router.post("/search/test", response_model=SearchTestResult)
async def test_search_provider(db: AsyncSession = Depends(get_db)) -> SearchTestResult:
    """Test the configured search provider with a sample query."""
    result = await deep_search_service.test_search(db, "recent M&A deals in technology")
    
    return SearchTestResult(
        success=result["success"],
        message=result["message"],
        result_count=result.get("result_count", 0)
    )


# ============================================================================
# MCP Server Endpoints
# ============================================================================

@router.get("/mcp", response_model=List[MCPServerConfigResponse])
async def get_mcp_servers(db: AsyncSession = Depends(get_db)) -> List[MCPServerConfigResponse]:
    """Get all MCP server configurations with connection status."""
    result = await db.execute(select(MCPServerConfig))
    configs = result.scalars().all()
    
    # Get current connection status from registry
    server_status = {s["server_type"]: s for s in mcp_registry.get_available_servers()}
    
    return [
        MCPServerConfigResponse(
            id=c.id,
            name=c.name,
            server_type=c.server_type,
            endpoint_url=c.endpoint_url,
            auth_token_masked=mask_api_key(decrypt_api_key(c.auth_token)) if c.auth_token else None,
            is_active=c.is_active,
            metadata=c.metadata,
            is_connected=server_status.get(c.server_type, {}).get("is_connected", False),
            tool_count=server_status.get(c.server_type, {}).get("tool_count", 0),
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in configs
    ]


@router.post("/mcp", response_model=MCPServerConfigResponse)
async def add_mcp_server(
    config_data: MCPServerConfigCreate,
    db: AsyncSession = Depends(get_db)
) -> MCPServerConfigResponse:
    """
    Add a new MCP server configuration.
    
    Attempts to connect to verify the server is reachable.
    Returns 422 if connection fails.
    """
    # Create config
    new_config = MCPServerConfig(
        name=config_data.name,
        server_type=config_data.server_type,
        endpoint_url=config_data.endpoint_url,
        auth_token=encrypt_api_key(config_data.auth_token) if config_data.auth_token else None,
        is_active=config_data.is_active,
        metadata=config_data.metadata
    )
    
    # Test connection before saving
    from app.services.mcp_registry import MCPClient, SECEdgarMCPClient, FinancialDataMCPClient, NewsMCPClient, SlackMCPClient, CustomMCPClient
    
    client_class = {
        "sec_edgar": SECEdgarMCPClient,
        "financial_data": FinancialDataMCPClient,
        "news": NewsMCPClient,
        "slack": SlackMCPClient,
        "custom": CustomMCPClient
    }.get(config_data.server_type)
    
    if client_class:
        test_client = client_class(new_config)
        connected = await test_client.connect()
        
        if not connected:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not connect to MCP server at {config_data.endpoint_url}. Please verify the URL and credentials."
            )
    
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    # Refresh registry
    await mcp_registry.refresh(db)
    
    logger.info(f"New MCP server added: {new_config.name} ({new_config.server_type})")
    
    return MCPServerConfigResponse(
        id=new_config.id,
        name=new_config.name,
        server_type=new_config.server_type,
        endpoint_url=new_config.endpoint_url,
        auth_token_masked=mask_api_key(config_data.auth_token),
        is_active=new_config.is_active,
        metadata=new_config.metadata,
        is_connected=True,
        tool_count=0,
        created_at=new_config.created_at,
        updated_at=new_config.updated_at
    )


@router.patch("/mcp/{server_id}/toggle", response_model=MCPServerConfigResponse)
async def toggle_mcp_server(
    server_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> MCPServerConfigResponse:
    """Toggle the active status of an MCP server."""
    result = await db.execute(select(MCPServerConfig).where(MCPServerConfig.id == server_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found"
        )
    
    config.is_active = not config.is_active
    await db.commit()
    await db.refresh(config)
    
    # Refresh registry
    await mcp_registry.refresh(db)
    
    server_status = {s["server_type"]: s for s in mcp_registry.get_available_servers()}
    
    return MCPServerConfigResponse(
        id=config.id,
        name=config.name,
        server_type=config.server_type,
        endpoint_url=config.endpoint_url,
        auth_token_masked=mask_api_key(decrypt_api_key(config.auth_token)) if config.auth_token else None,
        is_active=config.is_active,
        metadata=config.metadata,
        is_connected=server_status.get(config.server_type, {}).get("is_connected", False),
        tool_count=server_status.get(config.server_type, {}).get("tool_count", 0),
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.delete("/mcp/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(server_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete an MCP server configuration."""
    result = await db.execute(select(MCPServerConfig).where(MCPServerConfig.id == server_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found"
        )
    
    await db.delete(config)
    await db.commit()
    
    # Refresh registry
    await mcp_registry.refresh(db)
    
    logger.info(f"MCP server deleted: {config.name}")


# ============================================================================
# Settings Summary Endpoint
# ============================================================================

@router.get("/summary", response_model=SettingsSummary)
async def get_settings_summary(db: AsyncSession = Depends(get_db)) -> SettingsSummary:
    """Get a summary of all settings."""
    llm = await get_active_llm_config(db)
    search = await get_search_config(db)
    mcp = await get_mcp_servers(db)
    overrides = await get_agent_overrides(db)
    
    return SettingsSummary(
        llm_config=llm,
        search_config=search,
        mcp_servers=mcp,
        agent_overrides=overrides
    )


# ============================================================================
# Research Agent Endpoint
# ============================================================================

async def research_event_generator(
    request: ResearchRequest,
    db: AsyncSession
):
    """Generate SSE events for research agent."""
    async def streaming_callback(event_name: str, data: dict):
        yield {
            "event": event_name,
            "data": data
        }
    
    try:
        # Get LLM for research agent
        llm = await llm_factory.get_llm_for_agent("research", db)
        
        # Run research
        result = await run_research_agent(
            query=request.query,
            deal_id=request.deal_id,
            context=request.context,
            llm=llm,
            search_service=deep_search_service,
            streaming_callback=lambda name, data: streaming_callback(name, data)
        )
        
        # Yield final result
        yield {
            "event": "research_complete",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Research endpoint error: {e}")
        yield {
            "event": "agent_error",
            "data": {
                "message": f"Research failed: {str(e)}",
                "code": "RESEARCH_ERROR"
            }
        }


@router.post("/research")
async def run_research(
    request: ResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run the research agent for ad-hoc deep research.
    
    Returns SSE stream with progress events and final result.
    """
    return EventSourceResponse(research_event_generator(request, db))
