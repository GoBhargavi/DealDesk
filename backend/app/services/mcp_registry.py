"""
MCP (Model Context Protocol) Registry Service.

This module manages MCP server connections and exposes them as LangChain tools.
Supports bundled integrations: SEC EDGAR, Financial Data, News, Slack, and Custom servers.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx
from langchain.tools import StructuredTool
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.llm_config import MCPServerConfig
from app.services.llm_factory import decrypt_api_key

logger = logging.getLogger(__name__)


class MCPClient(ABC):
    """Abstract base class for MCP clients."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.endpoint_url = config.endpoint_url
        self.auth_token = decrypt_api_key(config.auth_token) if config.auth_token else None
        self.metadata = config.metadata or {}
        self._tools: List[BaseTool] = []
    
    @abstractmethod
    async def connect(self) -> bool:
        """Attempt to connect to the MCP server. Returns True on success."""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Return LangChain tools exposed by this MCP server."""
        pass
    
    async def _make_request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the MCP server."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        url = f"{self.endpoint_url.rstrip('/')}/{path.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"MCP request failed: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"MCP request error: {e}")
                raise


class SECEdgarMCPClient(MCPClient):
    """
    MCP client for SEC EDGAR filings.
    
    Exposes tools:
    - search_filings: Search SEC filings by company and form type
    - fetch_filing_document: Fetch full text of a filing
    - get_company_info: Get company information by ticker
    """
    
    async def connect(self) -> bool:
        """Test connection to SEC EDGAR MCP server."""
        try:
            # Try a simple search as connection test
            result = await self._make_request(
                "GET",
                "/health" if "/health" in self.endpoint_url else "/search",
                params={"query": "test", "limit": 1} if "/health" not in self.endpoint_url else None
            )
            return True
        except Exception as e:
            logger.warning(f"SEC EDGAR MCP connection failed: {e}")
            return False
    
    def get_tools(self) -> List[BaseTool]:
        """Return SEC EDGAR tools as LangChain tools."""
        
        class SearchFilingsInput(BaseModel):
            company: str = Field(..., description="Company name or ticker symbol")
            form_type: str = Field(default="10-K", description="SEC form type (10-K, 10-Q, 8-K, etc.)")
            date_from: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
        
        class FetchFilingInput(BaseModel):
            accession_number: str = Field(..., description="SEC accession number (e.g., '0000320193-23-000106')")
        
        class GetCompanyInfoInput(BaseModel):
            ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT')")
        
        async def search_filings(company: str, form_type: str = "10-K", date_from: Optional[str] = None) -> str:
            """Search SEC filings for a company."""
            try:
                params = {"company": company, "form_type": form_type}
                if date_from:
                    params["date_from"] = date_from
                
                result = await self._make_request("GET", "/filings/search", params=params)
                import json
                return json.dumps({"success": True, "filings": result.get("filings", [])})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e), "filings": []})
        
        async def fetch_filing_document(accession_number: str) -> str:
            """Fetch the full text of an SEC filing."""
            try:
                result = await self._make_request("GET", f"/filings/{accession_number}/document")
                import json
                return json.dumps({"success": True, "content": result.get("content", "")})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e), "content": ""})
        
        async def get_company_info(ticker: str) -> str:
            """Get company information from SEC EDGAR."""
            try:
                result = await self._make_request("GET", f"/companies/{ticker}")
                import json
                return json.dumps({"success": True, "company": result})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e)})
        
        tools = [
            StructuredTool.from_function(
                coroutine=search_filings,
                name="search_filings",
                description="Search SEC filings by company and form type",
                args_schema=SearchFilingsInput
            ),
            StructuredTool.from_function(
                coroutine=fetch_filing_document,
                name="fetch_filing_document",
                description="Fetch full text of an SEC filing by accession number",
                args_schema=FetchFilingInput
            ),
            StructuredTool.from_function(
                coroutine=get_company_info,
                name="get_company_info",
                description="Get company information by ticker symbol",
                args_schema=GetCompanyInfoInput
            )
        ]
        
        return tools
    
    async def search_filings_impl(
        self,
        company: str,
        form_type: str = "10-K",
        date_from: Optional[str] = None
    ) -> Dict[str, Any]:
        """Implementation of search_filings tool."""
        try:
            params = {"company": company, "form_type": form_type}
            if date_from:
                params["date_from"] = date_from
            
            result = await self._make_request("GET", "/filings/search", params=params)
            return {"success": True, "filings": result.get("filings", [])}
        except Exception as e:
            return {"success": False, "error": str(e), "filings": []}
    
    async def fetch_filing_impl(self, accession_number: str) -> Dict[str, Any]:
        """Implementation of fetch_filing_document tool."""
        try:
            result = await self._make_request(
                "GET",
                f"/filings/{accession_number}/document"
            )
            return {"success": True, "content": result.get("content", "")}
        except Exception as e:
            return {"success": False, "error": str(e), "content": ""}
    
    async def get_company_info_impl(self, ticker: str) -> Dict[str, Any]:
        """Implementation of get_company_info tool."""
        try:
            result = await self._make_request("GET", f"/companies/{ticker}")
            return {"success": True, "company": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


class FinancialDataMCPClient(MCPClient):
    """
    MCP client for financial market data.
    
    Exposes tools:
    - get_stock_price: Get current stock price
    - get_financial_ratios: Get valuation ratios (P/E, EV/EBITDA, etc.)
    - get_earnings_history: Get historical earnings data
    - get_peer_companies: Get list of peer companies
    """
    
    async def connect(self) -> bool:
        """Test connection to Financial Data MCP server."""
        try:
            # Try to get a stock price as connection test
            result = await self._make_request(
                "GET",
                "/health" if "/health" in self.endpoint_url else "/quote",
                params={"symbol": "AAPL"} if "/health" not in self.endpoint_url else None
            )
            return True
        except Exception as e:
            logger.warning(f"Financial Data MCP connection failed: {e}")
            return False
    
    def get_tools(self) -> List[BaseTool]:
        """Return Financial Data tools as LangChain tools."""
        
        class GetStockPriceInput(BaseModel):
            ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA')")
        
        class GetFinancialRatiosInput(BaseModel):
            ticker: str = Field(..., description="Stock ticker symbol")
        
        class GetEarningsHistoryInput(BaseModel):
            ticker: str = Field(..., description="Stock ticker symbol")
            years: int = Field(default=5, description="Number of years of history")
        
        class GetPeerCompaniesInput(BaseModel):
            ticker: str = Field(..., description="Stock ticker symbol")
        
        async def get_stock_price(ticker: str) -> str:
            """Get the current stock price for a company."""
            try:
                result = await self._make_request("GET", "/quote", params={"symbol": ticker})
                import json
                return json.dumps({
                    "success": True,
                    "ticker": ticker,
                    "price": result.get("price"),
                    "change": result.get("change"),
                    "change_percent": result.get("change_percent")
                })
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e)})
        
        async def get_financial_ratios(ticker: str) -> str:
            """Get financial valuation ratios for a company."""
            try:
                result = await self._make_request("GET", "/ratios", params={"symbol": ticker})
                import json
                return json.dumps({"success": True, "ticker": ticker, "ratios": result})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e)})
        
        async def get_earnings_history(ticker: str, years: int = 5) -> str:
            """Get historical earnings data for a company."""
            try:
                result = await self._make_request("GET", "/earnings", params={"symbol": ticker, "years": years})
                import json
                return json.dumps({"success": True, "ticker": ticker, "earnings": result.get("earnings", [])})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e)})
        
        async def get_peer_companies(ticker: str) -> str:
            """Get a list of peer companies for comparison."""
            try:
                result = await self._make_request("GET", "/peers", params={"symbol": ticker})
                import json
                return json.dumps({"success": True, "ticker": ticker, "peers": result.get("peers", [])})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e)})
        
        return [
            StructuredTool.from_function(
                coroutine=get_stock_price,
                name="get_stock_price",
                description="Get current stock price for a ticker",
                args_schema=GetStockPriceInput
            ),
            StructuredTool.from_function(
                coroutine=get_financial_ratios,
                name="get_financial_ratios",
                description="Get P/E, EV/EBITDA, and other valuation ratios",
                args_schema=GetFinancialRatiosInput
            ),
            StructuredTool.from_function(
                coroutine=get_earnings_history,
                name="get_earnings_history",
                description="Get historical earnings data",
                args_schema=GetEarningsHistoryInput
            ),
            StructuredTool.from_function(
                coroutine=get_peer_companies,
                name="get_peer_companies",
                description="Get list of peer companies",
                args_schema=GetPeerCompaniesInput
            )
        ]
    
    async def get_stock_price_impl(self, ticker: str) -> Dict[str, Any]:
        """Implementation of get_stock_price tool."""
        try:
            result = await self._make_request("GET", "/quote", params={"symbol": ticker})
            return {
                "success": True,
                "ticker": ticker,
                "price": result.get("price"),
                "change": result.get("change"),
                "change_percent": result.get("change_percent")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_financial_ratios_impl(self, ticker: str) -> Dict[str, Any]:
        """Implementation of get_financial_ratios tool."""
        try:
            result = await self._make_request("GET", "/ratios", params={"symbol": ticker})
            return {
                "success": True,
                "ticker": ticker,
                "ratios": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_earnings_history_impl(self, ticker: str, years: int = 5) -> Dict[str, Any]:
        """Implementation of get_earnings_history tool."""
        try:
            result = await self._make_request(
                "GET",
                "/earnings",
                params={"symbol": ticker, "years": years}
            )
            return {
                "success": True,
                "ticker": ticker,
                "earnings": result.get("earnings", [])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_peer_companies_impl(self, ticker: str) -> Dict[str, Any]:
        """Implementation of get_peer_companies tool."""
        try:
            result = await self._make_request("GET", "/peers", params={"symbol": ticker})
            return {
                "success": True,
                "ticker": ticker,
                "peers": result.get("peers", [])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class NewsMCPClient(MCPClient):
    """
    MCP client for financial news.
    
    Exposes tools:
    - search_news: Search news by query and date range
    - get_company_news: Get news for a specific company
    """
    
    async def connect(self) -> bool:
        """Test connection to News MCP server."""
        try:
            result = await self._make_request(
                "GET",
                "/health" if "/health" in self.endpoint_url else "/news",
                params={"query": "test", "limit": 1} if "/health" not in self.endpoint_url else None
            )
            return True
        except Exception as e:
            logger.warning(f"News MCP connection failed: {e}")
            return False
    
    def get_tools(self) -> List[BaseTool]:
        """Return News tools as LangChain tools."""
        
        class SearchNewsInput(BaseModel):
            query: str = Field(..., description="Search query string")
            from_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
            to_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
        
        class GetCompanyNewsInput(BaseModel):
            company_name: str = Field(..., description="Company name or ticker")
            days_back: int = Field(default=7, description="Number of days to look back")
        
        async def search_news(query: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> str:
            """Search for financial news articles."""
            try:
                params = {"query": query}
                if from_date:
                    params["from"] = from_date
                if to_date:
                    params["to"] = to_date
                
                result = await self._make_request("GET", "/news/search", params=params)
                import json
                return json.dumps({"success": True, "articles": result.get("articles", [])})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e), "articles": []})
        
        async def get_company_news(company_name: str, days_back: int = 7) -> str:
            """Get recent news for a specific company."""
            try:
                result = await self._make_request("GET", "/news/company", params={"company": company_name, "days": days_back})
                import json
                return json.dumps({"success": True, "company": company_name, "articles": result.get("articles", [])})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e), "articles": []})
        
        return [
            StructuredTool.from_function(
                coroutine=search_news,
                name="search_news",
                description="Search news by query and date range",
                args_schema=SearchNewsInput
            ),
            StructuredTool.from_function(
                coroutine=get_company_news,
                name="get_company_news",
                description="Get news for a specific company",
                args_schema=GetCompanyNewsInput
            )
        ]
    
    async def search_news_impl(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Implementation of search_news tool."""
        try:
            params = {"query": query}
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
            
            result = await self._make_request("GET", "/news/search", params=params)
            return {
                "success": True,
                "articles": result.get("articles", [])
            }
        except Exception as e:
            return {"success": False, "error": str(e), "articles": []}
    
    async def get_company_news_impl(self, company_name: str, days_back: int = 7) -> Dict[str, Any]:
        """Implementation of get_company_news tool."""
        try:
            result = await self._make_request(
                "GET",
                "/news/company",
                params={"company": company_name, "days": days_back}
            )
            return {
                "success": True,
                "company": company_name,
                "articles": result.get("articles", [])
            }
        except Exception as e:
            return {"success": False, "error": str(e), "articles": []}


class SlackMCPClient(MCPClient):
    """
    MCP client for Slack integration.
    
    Exposes tools:
    - post_message: Post a message to a Slack channel
    - post_deal_update: Post a formatted deal update
    """
    
    async def connect(self) -> bool:
        """Test connection to Slack MCP server."""
        try:
            result = await self._make_request("GET", "/health" if "/health" in self.endpoint_url else "/auth/test")
            return True
        except Exception as e:
            logger.warning(f"Slack MCP connection failed: {e}")
            return False
    
    def get_tools(self) -> List[BaseTool]:
        """Return Slack tools as LangChain tools."""
        
        class PostMessageInput(BaseModel):
            channel: str = Field(..., description="Channel name or ID (e.g., '#deals', 'C1234567890')")
            text: str = Field(..., description="Message text")
        
        class PostDealUpdateInput(BaseModel):
            deal_name: str = Field(..., description="Name of the deal")
            update: str = Field(..., description="Update text")
            channel: Optional[str] = Field(None, description="Channel to post to (defaults to configured channel)")
        
        async def post_message(channel: str, text: str) -> str:
            """Post a message to a Slack channel."""
            try:
                target_channel = channel or self.metadata.get("default_channel", "#general")
                result = await self._make_request("POST", "/chat.postMessage", json_data={"channel": target_channel, "text": text})
                import json
                return json.dumps({"success": True, "message": "Posted to Slack"})
            except Exception as e:
                import json
                return json.dumps({"success": False, "error": str(e)})
        
        async def post_deal_update(deal_name: str, update: str, channel: Optional[str] = None) -> str:
            """Post a formatted deal update to Slack."""
            formatted_text = f"*Deal Update: {deal_name}*\n>{update}"
            target = channel or self.metadata.get("deals_channel")
            return await post_message(target or "#general", formatted_text)
        
        return [
            StructuredTool.from_function(
                coroutine=post_message,
                name="post_message",
                description="Post a message to a Slack channel",
                args_schema=PostMessageInput
            ),
            StructuredTool.from_function(
                coroutine=post_deal_update,
                name="post_deal_update",
                description="Post a formatted deal update",
                args_schema=PostDealUpdateInput
            )
        ]
    
    async def post_message_impl(self, channel: str, text: str) -> Dict[str, Any]:
        """Implementation of post_message tool."""
        try:
            # Use default channel from metadata if not provided
            target_channel = channel or self.metadata.get("default_channel", "#general")
            
            result = await self._make_request(
                "POST",
                "/chat.postMessage",
                json_data={"channel": target_channel, "text": text}
            )
            return {"success": True, "message": "Posted to Slack"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def post_deal_update_impl(
        self,
        deal_name: str,
        update: str,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Implementation of post_deal_update tool."""
        formatted_text = f"*Deal Update: {deal_name}*\n>{update}"
        return await self.post_message_impl(channel or self.metadata.get("deals_channel"), formatted_text)


class CustomMCPClient(MCPClient):
    """
    Generic MCP client for custom/internal servers.
    Dynamically discovers available tools from the server's /tools endpoint.
    """
    
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)
        self._discovered_tools: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        """Connect to custom MCP server and discover tools."""
        try:
            result = await self._make_request("GET", "/tools")
            self._discovered_tools = result.get("tools", [])
            logger.info(f"Discovered {len(self._discovered_tools)} tools from custom MCP server")
            return True
        except Exception as e:
            logger.warning(f"Custom MCP connection failed: {e}")
            return False
    
    def get_tools(self) -> List[BaseTool]:
        """Return dynamically discovered tools as LangChain tools."""
        tools = []
        
        for tool_info in self._discovered_tools:
            tool_name = tool_info.get("name", "unknown_tool")
            tool_desc = tool_info.get("description", "No description")
            endpoint = tool_info.get("endpoint", f"/tools/{tool_name}")
            
            async def make_tool_func(endpoint_path: str):
                async def tool_func(**kwargs) -> str:
                    try:
                        result = await self._make_request("POST", endpoint_path, json_data=kwargs)
                        import json
                        return json.dumps(result)
                    except Exception as e:
                        return f"Error: {str(e)}"
                return tool_func
            
            func = make_tool_func(endpoint)
            
            tools.append(StructuredTool.from_function(
                coroutine=func,
                name=tool_name,
                description=tool_desc
            ))
        
        return tools


class MCPRegistry:
    """
    Registry for managing MCP server connections.
    
    Loads active MCPServerConfigs from the database on app startup,
    maintains connections, and exposes tools to agents.
    
    Agents call get_tools() to get available LangChain tools backed by MCP.
    If an MCP server is unavailable, it's marked inactive and skipped gracefully.
    """
    
    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._tools: Dict[str, List[BaseTool]] = {}
        self._server_status: Dict[str, Dict[str, Any]] = {}
    
    async def initialise(self, db: AsyncSession) -> None:
        """
        Load all active MCPServerConfigs from DB.
        For each, attempt connection and register tools.
        Log warnings for unreachable servers, do not raise.
        
        Args:
            db: Async database session
        """
        logger.info("Initializing MCP Registry...")
        
        result = await db.execute(
            select(MCPServerConfig).where(MCPServerConfig.is_active == True)
        )
        configs = result.scalars().all()
        
        for config in configs:
            try:
                client = self._create_client(config)
                if client is None:
                    logger.warning(f"Unknown MCP server type: {config.server_type}")
                    continue
                
                # Attempt connection
                connected = await client.connect()
                
                if connected:
                    self._clients[config.id.hex] = client
                    tools = client.get_tools()
                    self._tools[config.server_type] = tools
                    self._server_status[config.server_type] = {
                        "name": config.name,
                        "is_connected": True,
                        "tool_count": len(tools),
                        "last_error": None
                    }
                    logger.info(f"Connected to MCP server: {config.name} ({config.server_type})")
                else:
                    self._server_status[config.server_type] = {
                        "name": config.name,
                        "is_connected": False,
                        "tool_count": 0,
                        "last_error": "Connection failed"
                    }
                    logger.warning(f"Failed to connect to MCP server: {config.name}")
                    
            except Exception as e:
                logger.error(f"Error initializing MCP server {config.name}: {e}")
                self._server_status[config.server_type] = {
                    "name": config.name,
                    "is_connected": False,
                    "tool_count": 0,
                    "last_error": str(e)
                }
        
        logger.info(f"MCP Registry initialized with {len(self._clients)} active connections")
    
    def _create_client(self, config: MCPServerConfig) -> Optional[MCPClient]:
        """Create the appropriate MCP client based on server type."""
        if config.server_type == "sec_edgar":
            return SECEdgarMCPClient(config)
        elif config.server_type == "financial_data":
            return FinancialDataMCPClient(config)
        elif config.server_type == "news":
            return NewsMCPClient(config)
        elif config.server_type == "slack":
            return SlackMCPClient(config)
        elif config.server_type == "custom":
            return CustomMCPClient(config)
        else:
            return None
    
    def get_tools(self, server_types: Optional[List[str]] = None) -> List[BaseTool]:
        """
        Return all available LangChain tools from active MCP servers.
        
        Args:
            server_types: Optional list to filter by specific server types
            
        Returns:
            List of LangChain BaseTool instances
            Returns empty list if no servers are connected
        """
        all_tools: List[BaseTool] = []
        
        for server_type, tools in self._tools.items():
            if server_types is None or server_type in server_types:
                all_tools.extend(tools)
        
        return all_tools
    
    def get_available_servers(self) -> List[Dict[str, Any]]:
        """
        Return list of server status info for the settings UI.
        
        Returns:
            List of dicts with keys: server_type, name, is_connected, tool_count
        """
        return [
            {
                "server_type": server_type,
                "name": status["name"],
                "is_connected": status["is_connected"],
                "tool_count": status["tool_count"],
                "last_error": status.get("last_error")
            }
            for server_type, status in self._server_status.items()
        ]
    
    def is_server_connected(self, server_type: str) -> bool:
        """Check if a specific server type is connected."""
        status = self._server_status.get(server_type, {})
        return status.get("is_connected", False)
    
    async def refresh(self, db: AsyncSession) -> None:
        """Refresh all MCP connections from database."""
        self._clients.clear()
        self._tools.clear()
        self._server_status.clear()
        await self.initialise(db)


# Global registry instance
mcp_registry = MCPRegistry()
