"""
LLM Factory Service for Bring Your Own LLM (BYOLLM) capability.

This module provides a factory class that returns the correct LangChain ChatModel
based on the active LLMConfig in the database. Supports multiple providers with
encryption for API keys.
"""

import json
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.config import settings
from app.models.llm_config import LLMConfig, AgentLLMOverride
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)

# Redis cache TTL for LLM instances (5 minutes)
LLM_CACHE_TTL = 300

# Fernet instance for encryption/decryption
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """Get or create Fernet instance for encryption."""
    global _fernet
    if _fernet is None:
        # Use SECRET_KEY to derive a 32-byte key for Fernet
        import base64
        import hashlib
        key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_hash)
        _fernet = Fernet(fernet_key)
    return _fernet


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage."""
    if not api_key:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key from storage."""
    if not encrypted_key:
        return ""
    try:
        fernet = _get_fernet()
        return fernet.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {e}")
        raise ValueError("Credential decryption failed. Re-enter API key in Settings.") from e


def mask_api_key(api_key: Optional[str]) -> Optional[str]:
    """Mask an API key for display (e.g., sk-...****)."""
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "****"
    return api_key[:4] + "..." + api_key[-4:]


class LLMFactory:
    """
    Factory class for creating LangChain ChatModel instances based on configuration.
    
    Supports:
    - Anthropic Claude
    - OpenAI (GPT-4, GPT-3.5)
    - Google Gemini
    - Azure OpenAI
    - Ollama (local models)
    
    Caches instantiated models in Redis for 5 minutes to avoid DB hits.
    """
    
    def __init__(self):
        self._local_cache: dict = {}
    
    async def get_llm(self, db: AsyncSession) -> BaseChatModel:
        """
        Return the globally active LLM based on database configuration.
        
        Falls back to Anthropic Claude using ANTHROPIC_API_KEY from env
        if no active config is found in the database.
        
        Args:
            db: Async database session
            
        Returns:
            Configured LangChain ChatModel instance
            
        Raises:
            ValueError: If configuration is invalid or provider is unknown
        """
        # Try cache first
        cache_key = "llm_factory:active_llm"
        cached = await redis_service.get(cache_key)
        if cached:
            try:
                config_dict = json.loads(cached)
                return self._build_llm_from_dict(config_dict)
            except Exception:
                # Cache miss or corrupted, continue to DB
                pass
        
        # Query database for active config
        result = await db.execute(
            select(LLMConfig).where(LLMConfig.is_active == True)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            # Fallback to environment-based Anthropic config
            logger.warning("No active LLM config found, falling back to ANTHROPIC_API_KEY from env")
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("No LLM configuration found and ANTHROPIC_API_KEY not set")
            
            fallback_config = {
                "provider": "anthropic",
                "model_id": "claude-sonnet-4-20250514",
                "api_key": settings.ANTHROPIC_API_KEY,
                "base_url": None,
                "api_version": None
            }
            return self._build_llm_from_dict(fallback_config)
        
        # Build config dict with decrypted key
        config_dict = {
            "provider": config.provider,
            "model_id": config.model_id,
            "api_key": decrypt_api_key(config.api_key) if config.api_key else None,
            "base_url": config.base_url,
            "api_version": config.api_version
        }
        
        # Cache for 5 minutes (without the decrypted key for security)
        cache_dict = {**config_dict, "api_key": None}
        await redis_service.set(cache_key, json.dumps(cache_dict), ttl=LLM_CACHE_TTL)
        
        return self._build_llm_from_dict(config_dict)
    
    async def get_llm_for_agent(self, agent_name: str, db: AsyncSession) -> BaseChatModel:
        """
        Return the LLM for a specific agent, checking for agent-specific override.
        
        If an active override exists for the agent, use that LLM config.
        Otherwise, fall back to the global active LLM.
        
        Args:
            agent_name: Name of the agent (comps, dcf, news, document, pitchbook, research)
            db: Async database session
            
        Returns:
            Configured LangChain ChatModel instance
        """
        # Check cache for agent override
        cache_key = f"llm_factory:agent:{agent_name}"
        cached = await redis_service.get(cache_key)
        
        if cached:
            try:
                config_dict = json.loads(cached)
                return self._build_llm_from_dict(config_dict)
            except Exception:
                pass
        
        # Query for agent override
        result = await db.execute(
            select(AgentLLMOverride)
            .join(LLMConfig)
            .where(
                and_(
                    AgentLLMOverride.agent_name == agent_name,
                    AgentLLMOverride.is_active == True,
                    LLMConfig.is_active == True
                )
            )
        )
        override = result.scalar_one_or_none()
        
        if override and override.llm_config:
            config = override.llm_config
            config_dict = {
                "provider": config.provider,
                "model_id": config.model_id,
                "api_key": decrypt_api_key(config.api_key) if config.api_key else None,
                "base_url": config.base_url,
                "api_version": config.api_version
            }
            # Cache without decrypted key
            cache_dict = {**config_dict, "api_key": None}
            await redis_service.set(cache_key, json.dumps(cache_dict), ttl=LLM_CACHE_TTL)
            return self._build_llm_from_dict(config_dict)
        
        # No override, use global LLM
        return await self.get_llm(db)
    
    def _build_llm_from_dict(self, config_dict: dict) -> BaseChatModel:
        """Build LLM from a configuration dictionary."""
        return self._build_llm(
            provider=config_dict["provider"],
            model_id=config_dict["model_id"],
            api_key=config_dict.get("api_key"),
            base_url=config_dict.get("base_url"),
            api_version=config_dict.get("api_version")
        )
    
    def _build_llm(
        self,
        provider: str,
        model_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        api_version: Optional[str] = None
    ) -> BaseChatModel:
        """
        Instantiate the correct LangChain ChatModel for the given configuration.
        
        Args:
            provider: LLM provider name
            model_id: Model identifier
            api_key: API key (decrypted)
            base_url: Base URL for Azure OpenAI or Ollama
            api_version: API version for Azure OpenAI
            
        Returns:
            Configured LangChain ChatModel instance
            
        Raises:
            ValueError: If provider is unknown or required parameters are missing
        """
        if provider == "anthropic":
            if not api_key:
                raise ValueError("API key is required for Anthropic provider")
            return ChatAnthropic(
                model=model_id,
                api_key=api_key,
                temperature=0.1,
                max_tokens=4000
            )
        
        elif provider == "openai":
            if not api_key:
                raise ValueError("API key is required for OpenAI provider")
            return ChatOpenAI(
                model=model_id,
                api_key=api_key,
                temperature=0.1
            )
        
        elif provider == "google":
            if not api_key:
                raise ValueError("API key is required for Google provider")
            return ChatGoogleGenerativeAI(
                model=model_id,
                google_api_key=api_key,
                temperature=0.1
            )
        
        elif provider == "azure_openai":
            if not api_key:
                raise ValueError("API key is required for Azure OpenAI provider")
            if not base_url:
                raise ValueError("Base URL is required for Azure OpenAI provider")
            if not api_version:
                raise ValueError("API version is required for Azure OpenAI provider")
            return AzureChatOpenAI(
                azure_deployment=model_id,
                azure_endpoint=base_url,
                api_key=api_key,
                api_version=api_version,
                temperature=0.1
            )
        
        elif provider == "ollama":
            if not base_url:
                raise ValueError("Base URL is required for Ollama provider")
            return ChatOllama(
                model=model_id,
                base_url=base_url
            )
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    async def validate_config(self, config: LLMConfig) -> Tuple[bool, str]:
        """
        Test a configuration by making a minimal API call.
        
        Args:
            config: LLMConfig to validate
            
        Returns:
            Tuple of (success: bool, message: str)
            - On success: (True, "")
            - On failure: (False, error_message)
        """
        try:
            # Build LLM from config
            api_key = decrypt_api_key(config.api_key) if config.api_key else None
            llm = self._build_llm(
                provider=config.provider,
                model_id=config.model_id,
                api_key=api_key,
                base_url=config.base_url,
                api_version=config.api_version
            )
            
            # Make a simple test call
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content="Say 'hello' and nothing else.")]
            response = await llm.ainvoke(messages)
            
            # Check if we got a valid response
            if response and response.content:
                return True, ""
            else:
                return False, "Empty response from LLM"
                
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                return False, "Invalid API key. Please check your credentials."
            elif "model" in error_msg.lower():
                return False, f"Invalid model ID '{config.model_id}'. Please check the model name."
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                return False, f"Connection failed. Check your base URL ({config.base_url}) and network."
            else:
                return False, f"Validation failed: {error_msg}"
    
    async def invalidate_cache(self) -> None:
        """Clear the LLM cache in Redis. Call this after updating configs."""
        await redis_service.delete("llm_factory:active_llm")
        # Clear all agent-specific caches
        agents = ["comps", "dcf", "news", "document", "pitchbook", "research"]
        for agent in agents:
            await redis_service.delete(f"llm_factory:agent:{agent}")
        logger.info("LLM factory cache cleared")


# Global factory instance
llm_factory = LLMFactory()
