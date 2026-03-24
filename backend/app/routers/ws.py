"""WebSocket router for real-time updates."""

import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.redis_service import get_redis_client, RedisPubSub

router = APIRouter(prefix="/ws", tags=["websocket"])

# Connection manager for WebSocket clients
class ConnectionManager:
    """Manages WebSocket connections and Redis Pub/Sub."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_pubsub: RedisPubSub = RedisPubSub()
        self._listener_task: asyncio.Task = None
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Start Redis listener if not already running
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._redis_listener())
    
    def disconnect(self, client_id: str) -> None:
        """Remove a disconnected client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        disconnected = []
        
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def send_personal_message(self, message: dict, client_id: str) -> None:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception:
                self.disconnect(client_id)
    
    async def _redis_listener(self) -> None:
        """Listen for Redis Pub/Sub events and broadcast to WebSocket clients."""
        try:
            await self.redis_pubsub.subscribe()
            
            async for message in self.redis_pubsub.listen():
                if message:
                    await self.broadcast(message)
                    
        except asyncio.CancelledError:
            await self.redis_pubsub.unsubscribe()
        except Exception:
            await self.redis_pubsub.unsubscribe()


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time updates.
    
    Path Parameters:
    - **client_id**: Unique client identifier
    
    ## WebSocket Events
    
    ### Incoming (Client → Server)
    - `ping`: Keep-alive ping, server responds with `pong`
    - `subscribe_deal`: Subscribe to updates for a specific deal
    
    ### Outgoing (Server → Client)
    - `deal_stage_changed`: Deal moved to new stage
      ```json
      {
        "event": "deal_stage_changed",
        "deal_id": "...",
        "from_stage": "Diligence",
        "to_stage": "LOI"
      }
      ```
    - `deal_created`: New deal added to pipeline
      ```json
      {
        "event": "deal_created",
        "deal": { ... }
      }
      ```
    - `deal_updated`: Deal fields modified
      ```json
      {
        "event": "deal_updated",
        "deal_id": "...",
        "fields": ["deal_value_usd", "stage"]
      }
      ```
    - `agent_started`: AI agent began processing
      ```json
      {
        "event": "agent_started",
        "job_id": "...",
        "agent": "comps",
        "deal_id": "..."
      }
      ```
    - `agent_done`: AI agent completed processing
      ```json
      {
        "event": "agent_done",
        "job_id": "...",
        "agent": "comps",
        "deal_id": "..."
      }
      ```
    - `document_ready`: Document processing complete
      ```json
      {
        "event": "document_ready",
        "document_id": "...",
        "deal_id": "..."
      }
      ```
    - `pong`: Response to client ping
    """
    await manager.connect(websocket, client_id)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            {"event": "connected", "client_id": client_id},
            client_id
        )
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                event_type = message.get("event")
                
                if event_type == "ping":
                    await manager.send_personal_message(
                        {"event": "pong"},
                        client_id
                    )
                elif event_type == "subscribe_deal":
                    deal_id = message.get("deal_id")
                    await manager.send_personal_message(
                        {"event": "subscribed", "deal_id": deal_id},
                        client_id
                    )
                else:
                    # Echo unknown events back
                    await manager.send_personal_message(
                        {"event": "echo", "data": message},
                        client_id
                    )
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"event": "error", "message": "Invalid JSON"},
                    client_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception:
        manager.disconnect(client_id)
