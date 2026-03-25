"""
Deep Search Service for multi-step web research.

This module implements the DeepSearchService which orchestrates a research pipeline
for agents that need real-world data instead of hallucinated responses.

Pipeline:
  1. Query Generation - LLM generates targeted search queries
  2. Parallel Search - Execute all queries simultaneously
  3. Source Fetching - Extract content from top results
  4. Synthesis - LLM synthesizes findings into structured output

Supports multiple search providers: Tavily, Perplexity, Exa AI
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.llm_config import SearchConfig
from app.services.llm_factory import decrypt_api_key

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

try:
    from exa_py import Exa
except ImportError:
    Exa = None

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result with metadata."""
    url: str
    title: str
    snippet: str
    full_content: Optional[str] = None
    source_name: str = ""
    published_date: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class ResearchContext:
    """Context for a research session."""
    task: str
    queries: List[str]
    sources: List[SearchResult]
    output_schema: Dict[str, Any]


class DeepSearchService:
    """
    Multi-step web research service for agents needing real-world data.
    
    Each step emits SSE events so the frontend can show live progress:
    - "generating_queries" - Creating targeted search queries
    - "searching" - Executing parallel searches
    - "fetching_sources" - Reading full page content
    - "synthesising" - Combining findings into output
    - "done" - Research complete
    """
    
    def __init__(self):
        self._search_clients: Dict[str, Any] = {}
    
    async def research(
        self,
        task: str,
        context: Dict[str, Any],
        output_schema: Dict[str, Any],
        llm: BaseChatModel,
        db: AsyncSession,
        streaming_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Run the full research pipeline.
        
        Args:
            task: Natural language description of what to research
            context: Additional context (company name, sector, deal type, etc.)
            output_schema: JSON schema dict describing expected output structure
            llm: LangChain ChatModel to use for query generation and synthesis
            db: Database session to load search configuration
            streaming_callback: Async function called at each pipeline step
            
        Returns:
            Dict matching output_schema with research findings
            
        Emits SSE events:
            - research_step: {step, message, ...}
            - research_done: {step: "done", source_count, query_count}
        """
        try:
            # Step 1: Generate queries
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "generating_queries",
                    "message": "Generating targeted search queries..."
                })
            
            queries = await self._generate_queries(task, context, llm)
            
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "searching",
                    "message": f"Searching {len(queries)} queries in parallel...",
                    "query_count": len(queries)
                })
            
            # Step 2: Execute searches
            raw_results = await self._execute_searches(queries, db)
            
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "fetching_sources",
                    "message": f"Reading {len(raw_results)} sources...",
                    "source_count": len(raw_results)
                })
            
            # Step 3: Fetch full content if enabled
            search_config = await self._get_search_config(db)
            if search_config and search_config.enable_full_page_fetch:
                await self._fetch_full_content(raw_results)
            
            if streaming_callback:
                await streaming_callback("research_step", {
                    "step": "synthesising",
                    "message": "Synthesizing findings..."
                })
            
            # Step 4: Synthesize results
            result = await self._synthesize(task, raw_results, output_schema, llm)
            
            if streaming_callback:
                await streaming_callback("research_done", {
                    "step": "done",
                    "source_count": len(raw_results),
                    "query_count": len(queries)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Deep search failed: {e}")
            # Fall back to LLM-only generation with warning flag
            logger.warning("Falling back to LLM-only generation due to search failure")
            fallback_result = await self._fallback_synthesis(task, context, output_schema, llm)
            fallback_result["data_source"] = "llm_generated"
            return fallback_result
    
    async def _generate_queries(
        self,
        task: str,
        context: Dict[str, Any],
        llm: BaseChatModel
    ) -> List[str]:
        """
        Use LLM to generate 3-5 targeted search queries for the task.
        
        Args:
            task: Research task description
            context: Additional context
            llm: Chat model for query generation
            
        Returns:
            List of search query strings
        """
        system_prompt = """You are a research assistant for investment banking. 
Generate 3-5 targeted search queries to find relevant information for the given task.

Rules:
- Queries should be specific and targeted
- Use financial/industry terminology appropriate for investment banking
- Include date ranges when relevant (e.g., "2022-2025")
- Each query should cover a different angle of the research
- Return ONLY a JSON array of query strings, no other text

Example output: ["query 1", "query 2", "query 3"]"""

        context_str = "\n".join([f"- {k}: {v}" for k, v in context.items() if v])
        
        user_prompt = f"""Task: {task}

Context:
{context_str}

Generate 3-5 search queries as a JSON array:"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            # Extract JSON array from response
            import json
            # Handle markdown code blocks
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
            
            queries = json.loads(content)
            
            if isinstance(queries, list) and len(queries) > 0:
                return queries[:5]  # Max 5 queries
            else:
                logger.warning("Invalid query generation response, using fallback")
                return self._fallback_queries(task, context)
                
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            return self._fallback_queries(task, context)
    
    def _fallback_queries(self, task: str, context: Dict[str, Any]) -> List[str]:
        """Generate fallback queries when LLM generation fails."""
        queries = [task]  # Always include the task itself
        
        # Add context-based queries
        if context.get("company_name"):
            queries.append(f"{context['company_name']} news recent")
        if context.get("sector"):
            queries.append(f"{context['sector']} M&A transactions 2024 2025")
        if context.get("deal_type"):
            queries.append(f"{context['deal_type']} deals market trends")
        
        return queries[:5]
    
    async def _execute_searches(
        self,
        queries: List[str],
        db: AsyncSession
    ) -> List[SearchResult]:
        """
        Execute all queries in parallel against the configured search provider.
        
        Args:
            queries: List of search query strings
            db: Database session to load search config
            
        Returns:
            Merged, deduplicated list of search results
        """
        search_config = await self._get_search_config(db)
        
        if not search_config:
            logger.error("No active search configuration found")
            raise ValueError("No search provider configured. Please configure a search provider in Settings.")
        
        # Execute all queries in parallel
        tasks = [
            self._search_with_provider(query, search_config)
            for query in queries
        ]
        
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge and deduplicate results
        all_results: Dict[str, SearchResult] = {}
        for results in results_lists:
            if isinstance(results, Exception):
                logger.error(f"Search query failed: {results}")
                continue
            for result in results:
                if result.url not in all_results:
                    all_results[result.url] = result
                else:
                    # Keep higher relevance score
                    if result.relevance_score > all_results[result.url].relevance_score:
                        all_results[result.url] = result
        
        # Sort by relevance and limit
        max_results = search_config.max_results_per_query * len(queries)
        sorted_results = sorted(
            all_results.values(),
            key=lambda r: r.relevance_score,
            reverse=True
        )[:max_results]
        
        return sorted_results
    
    async def _get_search_config(self, db: AsyncSession) -> Optional[SearchConfig]:
        """Load active search configuration from database."""
        result = await db.execute(
            select(SearchConfig).where(SearchConfig.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def _search_with_provider(
        self,
        query: str,
        config: SearchConfig
    ) -> List[SearchResult]:
        """Execute a search using the configured provider."""
        if config.provider == "tavily":
            return await self._search_tavily(query, config)
        elif config.provider == "perplexity":
            return await self._search_perplexity(query, config)
        elif config.provider == "exa":
            return await self._search_exa(query, config)
        else:
            raise ValueError(f"Unknown search provider: {config.provider}")
    
    async def _search_tavily(self, query: str, config: SearchConfig) -> List[SearchResult]:
        """Search using Tavily API."""
        try:
            api_key = decrypt_api_key(config.api_key) if config.api_key else None
            if not api_key:
                raise ValueError("Tavily API key not configured")
            
            if TavilyClient is None:
                raise ImportError("tavily-python package not installed")
            
            client = TavilyClient(api_key=api_key)
            
            # Run synchronous client in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.search(
                    query=query,
                    max_results=config.max_results_per_query,
                    search_depth="advanced" if config.enable_full_page_fetch else "basic"
                )
            )
            
            results = []
            for item in response.get("results", []):
                results.append(SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("content", ""),
                    source_name="Tavily",
                    relevance_score=item.get("score", 0.0)
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
    
    async def _search_perplexity(self, query: str, config: SearchConfig) -> List[SearchResult]:
        """Search using Perplexity API."""
        try:
            api_key = decrypt_api_key(config.api_key) if config.api_key else None
            if not api_key:
                raise ValueError("Perplexity API key not configured")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that provides accurate information with citations."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse Perplexity response with citations
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            
            results = []
            for i, citation in enumerate(citations[:config.max_results_per_query]):
                results.append(SearchResult(
                    url=citation if isinstance(citation, str) else citation.get("url", ""),
                    title=f"Source {i+1}",
                    snippet=content[:500] if i == 0 else "",
                    source_name="Perplexity",
                    relevance_score=1.0 - (i * 0.1)
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Perplexity search failed: {e}")
            return []
    
    async def _search_exa(self, query: str, config: SearchConfig) -> List[SearchResult]:
        """Search using Exa AI API."""
        try:
            api_key = decrypt_api_key(config.api_key) if config.api_key else None
            if not api_key:
                raise ValueError("Exa AI API key not configured")
            
            if Exa is None:
                raise ImportError("exa-py package not installed")
            
            exa = Exa(api_key=api_key)
            
            # Run synchronous client in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: exa.search_and_contents(
                    query,
                    type="auto",
                    num_results=config.max_results_per_query,
                    highlights=True
                )
            )
            
            results = []
            for result in response.results:
                results.append(SearchResult(
                    url=result.url,
                    title=result.title if hasattr(result, 'title') else result.url,
                    snippet=result.text[:500] if hasattr(result, 'text') else "",
                    source_name="Exa AI",
                    published_date=result.published_date if hasattr(result, 'published_date') else None,
                    relevance_score=result.score if hasattr(result, 'score') else 0.5
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Exa search failed: {e}")
            return []
    
    async def _fetch_full_content(self, results: List[SearchResult]) -> None:
        """Fetch and extract full page content from URLs."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(10.0, connect=5.0),
            headers={"User-Agent": "Mozilla/5.0 (compatible; DealDesk Bot)"}
        ) as client:
            tasks = [self._fetch_single_page(client, result) for result in results]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_single_page(
        self,
        client: httpx.AsyncClient,
        result: SearchResult
    ) -> None:
        """Fetch content from a single URL."""
        try:
            response = await client.get(result.url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text(separator=' ', strip=True)
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                result.full_content = ' '.join(chunk for chunk in chunks if chunk)[:10000]  # Limit length
                
        except Exception as e:
            logger.warning(f"Failed to fetch {result.url}: {e}")
            # Leave full_content as None
    
    async def _synthesize(
        self,
        task: str,
        sources: List[SearchResult],
        output_schema: Dict[str, Any],
        llm: BaseChatModel
    ) -> Dict[str, Any]:
        """
        Feed all source content to the LLM and extract structured output.
        
        Args:
            task: Original research task
            sources: List of search results with content
            output_schema: Expected output structure
            llm: Chat model for synthesis
            
        Returns:
            Dict matching output_schema with synthesized findings
        """
        # Build context from sources
        source_texts = []
        for i, source in enumerate(sources, 1):
            content = source.full_content or source.snippet
            source_texts.append(f"""Source {i}: {source.title}
URL: {source.url}
Content: {content[:2000]}  # Limit per source
---""")
        
        sources_text = "\n\n".join(source_texts)
        
        system_prompt = f"""You are an investment banking research analyst. 
Synthesize the provided sources into a structured response matching the required schema.

Task: {task}

Required output format (JSON):
{output_schema}

Rules:
- Only use information from the provided sources
- Cite specific sources when making claims
- If information is missing, indicate "not found" or null
- Return valid JSON matching the schema exactly
- Be concise but comprehensive
- Use professional investment banking terminology"""

        user_prompt = f"""Sources:
{sources_text}

Synthesize this information into the required format. Return only valid JSON:"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            # Extract JSON from response
            import json
            if "```" in content:
                # Extract from code block
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            result["data_source"] = "web_research"
            result["_sources_used"] = len(sources)
            
            return result
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return await self._fallback_synthesis(task, {}, output_schema, llm)
    
    async def _fallback_synthesis(
        self,
        task: str,
        context: Dict[str, Any],
        output_schema: Dict[str, Any],
        llm: BaseChatModel
    ) -> Dict[str, Any]:
        """Generate fallback response using only LLM when search fails."""
        context_str = "\n".join([f"- {k}: {v}" for k, v in context.items() if v])
        
        system_prompt = f"""You are an investment banking AI assistant. 
The search service is currently unavailable. Generate a response based on your training knowledge,
but clearly indicate this is AI-generated without live research.

Required output format (JSON):
{output_schema}

Add these fields:
- "data_source": "llm_generated"
- "caveats": explanation that this is AI-generated and may not reflect latest market data

Return valid JSON only."""

        user_prompt = f"""Task: {task}
Context:
{context_str}

Generate a response. Acknowledge this is based on training data, not live research:"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            import json
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            result["data_source"] = "llm_generated"
            result["caveats"] = result.get("caveats", "This response was generated using AI training data without live web research. Market conditions may have changed.")
            
            return result
            
        except Exception as e:
            logger.error(f"Fallback synthesis failed: {e}")
            # Return minimal valid response
            return {
                "data_source": "llm_generated",
                "caveats": "Unable to generate complete response due to service unavailability.",
                "error": "Synthesis failed"
            }
    
    async def test_search(self, db: AsyncSession, test_query: str = "recent M&A deals in technology") -> Dict[str, Any]:
        """
        Test the configured search provider with a simple query.
        
        Args:
            db: Database session
            test_query: Query string to test with
            
        Returns:
            Dict with success status, message, and result count
        """
        try:
            config = await self._get_search_config(db)
            if not config:
                return {
                    "success": False,
                    "message": "No search provider configured",
                    "result_count": 0
                }
            
            results = await self._search_with_provider(test_query, config)
            
            return {
                "success": True,
                "message": f"Search successful using {config.provider}",
                "result_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Search test failed: {e}")
            return {
                "success": False,
                "message": f"Search test failed: {str(e)}",
                "result_count": 0
            }


# Global service instance
deep_search_service = DeepSearchService()
