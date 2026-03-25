"""
LLM Configuration, Search Configuration, and MCP Server Configuration models.

This module defines the database models for Bring Your Own LLM (BYOLLM),
Deep Search, and MCP Server capabilities in DealDesk.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class LLMConfig(Base):
    """Configuration for LLM providers (BYOLLM)."""
    
    __tablename__ = "llm_configs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False)  # anthropic, openai, google, azure_openai, ollama
    model_id = Column(String(100), nullable=False)
    api_key = Column(Text, nullable=True)  # encrypted at rest
    base_url = Column(String(500), nullable=True)  # required for azure_openai and ollama
    api_version = Column(String(50), nullable=True)  # required for azure_openai
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    agent_overrides = relationship("AgentLLMOverride", back_populates="llm_config", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<LLMConfig(id={self.id}, provider={self.provider}, model={self.model_id}, active={self.is_active})>"


class AgentLLMOverride(Base):
    """Per-agent LLM model overrides."""
    
    __tablename__ = "agent_llm_overrides"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(50), nullable=False)  # comps, dcf, news, document, pitchbook, research
    llm_config_id = Column(PGUUID(as_uuid=True), ForeignKey("llm_configs.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    llm_config = relationship("LLMConfig", back_populates="agent_overrides")
    
    def __repr__(self) -> str:
        return f"<AgentLLMOverride(agent={self.agent_name}, config_id={self.llm_config_id}, active={self.is_active})>"


class SearchConfig(Base):
    """Configuration for Deep Search providers."""
    
    __tablename__ = "search_configs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False)  # tavily, perplexity, exa
    api_key = Column(Text, nullable=True)  # encrypted at rest
    max_results_per_query = Column(Integer, default=5, nullable=False)
    max_queries_per_task = Column(Integer, default=5, nullable=False)
    enable_full_page_fetch = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<SearchConfig(provider={self.provider}, active={self.is_active})>"


class MCPServerConfig(Base):
    """Configuration for MCP (Model Context Protocol) server connections."""
    
    __tablename__ = "mcp_server_configs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # human-readable name
    server_type = Column(String(50), nullable=False)  # sec_edgar, financial_data, news, slack, custom
    endpoint_url = Column(String(500), nullable=False)  # MCP server URL
    auth_token = Column(Text, nullable=True)  # encrypted at rest
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, default=dict)  # extra config per server type
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<MCPServerConfig(name={self.name}, type={self.server_type}, active={self.is_active})>"
