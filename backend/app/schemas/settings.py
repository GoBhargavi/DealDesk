"""
Pydantic schemas for settings management (BYOLLM, Deep Search, MCP).

Includes schemas for LLMConfig, SearchConfig, MCPServerConfig, and agent overrides.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ============================================================================
# LLM Provider Schemas
# ============================================================================

class LLMConfigBase(BaseModel):
    """Base schema for LLM configuration."""
    provider: str = Field(..., description="Provider: anthropic, openai, google, azure_openai, ollama")
    model_id: str = Field(..., description="Model identifier (e.g., claude-sonnet-4-20250514)")
    base_url: Optional[str] = Field(None, description="Base URL for Azure OpenAI or Ollama")
    api_version: Optional[str] = Field(None, description="API version for Azure OpenAI")
    is_active: bool = Field(True, description="Whether this config is active")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['anthropic', 'openai', 'google', 'azure_openai', 'ollama']
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {', '.join(allowed)}")
        return v


class LLMConfigCreate(LLMConfigBase):
    """Schema for creating a new LLM config."""
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")


class LLMConfigUpdate(BaseModel):
    """Schema for updating an existing LLM config."""
    provider: Optional[str] = None
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    is_active: Optional[bool] = None


class LLMConfigResponse(LLMConfigBase):
    """Schema for returning LLM config (with masked API key)."""
    id: UUID
    api_key_masked: Optional[str] = Field(None, description="Masked API key (e.g., sk-...****)")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LLMProviderInfo(BaseModel):
    """Information about a supported LLM provider."""
    id: str
    label: str
    models: List[str]
    required_fields: List[str]
    optional_fields: List[str]


# ============================================================================
# Agent Override Schemas
# ============================================================================

class AgentLLMOverrideBase(BaseModel):
    """Base schema for agent LLM override."""
    agent_name: str = Field(..., description="Agent name: comps, dcf, news, document, pitchbook, research")
    llm_config_id: UUID
    is_active: bool = Field(True)
    
    @validator('agent_name')
    def validate_agent_name(cls, v):
        allowed = ['comps', 'dcf', 'news', 'document', 'pitchbook', 'research']
        if v not in allowed:
            raise ValueError(f"Agent name must be one of: {', '.join(allowed)}")
        return v


class AgentLLMOverrideCreate(AgentLLMOverrideBase):
    """Schema for creating an agent LLM override."""
    pass


class AgentLLMOverrideResponse(AgentLLMOverrideBase):
    """Schema for returning agent LLM override."""
    id: UUID
    llm_config: Optional[LLMConfigResponse] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentOverrideUpdate(BaseModel):
    """Schema for updating an agent override."""
    llm_config_id: Optional[UUID] = None
    is_active: Optional[bool] = None


# ============================================================================
# Search Provider Schemas
# ============================================================================

class SearchConfigBase(BaseModel):
    """Base schema for search configuration."""
    provider: str = Field(..., description="Provider: tavily, perplexity, exa")
    max_results_per_query: int = Field(5, ge=1, le=10)
    max_queries_per_task: int = Field(5, ge=1, le=10)
    enable_full_page_fetch: bool = Field(True)
    is_active: bool = Field(True)
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['tavily', 'perplexity', 'exa']
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {', '.join(allowed)}")
        return v


class SearchConfigCreate(SearchConfigBase):
    """Schema for creating a new search config."""
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")


class SearchConfigUpdate(BaseModel):
    """Schema for updating an existing search config."""
    provider: Optional[str] = None
    api_key: Optional[str] = None
    max_results_per_query: Optional[int] = None
    max_queries_per_task: Optional[int] = None
    enable_full_page_fetch: Optional[bool] = None
    is_active: Optional[bool] = None


class SearchConfigResponse(SearchConfigBase):
    """Schema for returning search config (with masked API key)."""
    id: UUID
    api_key_masked: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SearchTestResult(BaseModel):
    """Result of a search provider test."""
    success: bool
    message: str
    result_count: Optional[int] = None


# ============================================================================
# MCP Server Schemas
# ============================================================================

class MCPServerConfigBase(BaseModel):
    """Base schema for MCP server configuration."""
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name")
    server_type: str = Field(..., description="Type: sec_edgar, financial_data, news, slack, custom")
    endpoint_url: str = Field(..., description="MCP server URL")
    is_active: bool = Field(True)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('server_type')
    def validate_server_type(cls, v):
        allowed = ['sec_edgar', 'financial_data', 'news', 'slack', 'custom']
        if v not in allowed:
            raise ValueError(f"Server type must be one of: {', '.join(allowed)}")
        return v


class MCPServerConfigCreate(MCPServerConfigBase):
    """Schema for creating a new MCP server config."""
    auth_token: Optional[str] = Field(None, description="Auth token (will be encrypted)")


class MCPServerConfigUpdate(BaseModel):
    """Schema for updating an MCP server config."""
    name: Optional[str] = None
    endpoint_url: Optional[str] = None
    auth_token: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPServerStatus(BaseModel):
    """Status information for an MCP server."""
    server_type: str
    name: str
    is_connected: bool
    tool_count: int
    last_error: Optional[str] = None


class MCPServerConfigResponse(MCPServerConfigBase):
    """Schema for returning MCP server config."""
    id: UUID
    auth_token_masked: Optional[str] = None
    is_connected: bool = False
    tool_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Combined Settings Response
# ============================================================================

class SettingsSummary(BaseModel):
    """Summary of all settings."""
    llm_config: Optional[LLMConfigResponse] = None
    search_config: Optional[SearchConfigResponse] = None
    mcp_servers: List[MCPServerConfigResponse] = Field(default_factory=list)
    agent_overrides: List[AgentLLMOverrideResponse] = Field(default_factory=list)


# ============================================================================
# Research Agent Request/Response
# ============================================================================

class ResearchRequest(BaseModel):
    """Request body for the research agent."""
    deal_id: str = Field(..., description="Deal ID for context")
    query: str = Field(..., min_length=5, description="Research question")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Source(BaseModel):
    """A cited source in research results."""
    url: str
    title: str
    source_name: str
    published_date: Optional[str] = None
    relevance_score: float


class ResearchResult(BaseModel):
    """Response from the research agent."""
    query: str
    summary: str
    key_findings: List[str]
    sources: List[Source]
    confidence: str = Field(..., regex="^(high|medium|low)$")
    caveats: Optional[str] = None
    data_source: str = Field(..., regex="^(web_research|llm_generated)$")


# ============================================================================
# Validation Response
# ============================================================================

class ValidationResult(BaseModel):
    """Result of validating a configuration."""
    valid: bool
    message: str
