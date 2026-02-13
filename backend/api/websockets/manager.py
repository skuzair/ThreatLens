from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Different channels for different dashboard sections
        self.alert_connections: List[WebSocket] = []
        self.live_connections: Dict[str, List[WebSocket]] = {
            "network": [],
            "camera": [],
            "rf": [],
            "logs": [],
            "files": []
        }
    
    async def connect_alerts(self, websocket: WebSocket):
        """Connect a client to the alerts feed"""
        await websocket.accept()
        self.alert_connections.append(websocket)
        print(f"🔌 Alert client connected. Total: {len(self.alert_connections)}")
    
    async def connect_live(self, websocket: WebSocket, source: str):
        """Connect a client to a specific live data source"""
        await websocket.accept()
        if source in self.live_connections:
            self.live_connections[source].append(websocket)
            print(f"🔌 Live:{source} client connected. Total: {len(self.live_connections[source])}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a disconnected client from all channels"""
        if websocket in self.alert_connections:
            self.alert_connections.remove(websocket)
            print(f"🔌 Alert client disconnected. Remaining: {len(self.alert_connections)}")
        
        for source_list in self.live_connections.values():
            if websocket in source_list:
                source_list.remove(websocket)
    
    async def broadcast_to_alerts(self, message: dict):
        """Broadcast a message to all alert feed clients"""
        dead_connections = []
        for websocket in self.alert_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to alert client: {e}")
                dead_connections.append(websocket)
        
        # Clean up dead connections
        for ws in dead_connections:
            self.alert_connections.remove(ws)
    
    async def broadcast_to_live(self, source: str, message: dict):
        """Broadcast a message to all clients of a specific live source"""
        dead_connections = []
        for websocket in self.live_connections.get(source, []):
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to live:{source} client: {e}")
                dead_connections.append(websocket)
        
        # Clean up dead connections
        for ws in dead_connections:
            if ws in self.live_connections[source]:
                self.live_connections[source].remove(ws)
    
    def get_connection_stats(self) -> dict:
        """Get current connection statistics"""
        return {
            "alerts": len(self.alert_connections),
            "live": {
                source: len(connections) 
                for source, connections in self.live_connections.items()
            }
        }


# Global websocket manager instance
websocket_manager = WebSocketManager()
