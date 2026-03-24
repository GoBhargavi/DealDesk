"""Redis service for pub/sub and caching."""

import json
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
from app.config import get_settings

settings = get_settings()

# Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    return _redis_client


async def close_redis_connection() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def publish_event(channel: str, event: Dict[str, Any]) -> None:
    """
    Publish an event to a Redis channel.
    
    Args:
        channel: Redis channel name
        event: Event data as dictionary
    """
    client = await get_redis_client()
    await client.publish(channel, json.dumps(event))


async def cache_set(key: str, value: Any, expire: int = 3600) -> None:
    """
    Set a value in Redis cache.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expire: TTL in seconds (default 1 hour)
    """
    client = await get_redis_client()
    await client.setex(key, expire, json.dumps(value))


async def cache_get(key: str) -> Optional[Any]:
    """
    Get a value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    client = await get_redis_client()
    value = await client.get(key)
    if value:
        return json.loads(value)
    return None


async def cache_delete(key: str) -> None:
    """
    Delete a key from Redis cache.
    
    Args:
        key: Cache key to delete
    """
    client = await get_redis_client()
    await client.delete(key)


class RedisPubSub:
    """Redis Pub/Sub manager for WebSocket broadcasting."""
    
    def __init__(self, channel: str = "dealdesk:events"):
        self.channel = channel
        self._pubsub: Optional[redis.client.PubSub] = None
        self._listeners: List[Any] = []
    
    async def subscribe(self) -> None:
        """Subscribe to the events channel."""
        client = await get_redis_client()
        self._pubsub = client.pubsub()
        await self._pubsub.subscribe(self.channel)
    
    async def unsubscribe(self) -> None:
        """Unsubscribe from the events channel."""
        if self._pubsub:
            await self._pubsub.unsubscribe(self.channel)
            await self._pubsub.close()
            self._pubsub = None
    
    async def listen(self):
        """Listen for messages on the channel."""
        if self._pubsub:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError:
                        continue
    
    async def publish(self, event: Dict[str, Any]) -> None:
        """Publish an event to the channel."""
        await publish_event(self.channel, event)
