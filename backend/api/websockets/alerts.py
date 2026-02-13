from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websockets.manager import websocket_manager

router = APIRouter()


@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time alert feed"""
    await websocket_manager.connect_alerts(websocket)
    try:
        # Keep connection alive and listen for any client messages
        while True:
            try:
                # Receive text to keep connection alive
                data = await websocket.receive_text()
                # Echo back connection status if requested
                if data == "ping":
                    await websocket.send_json({"type": "pong", "connections": websocket_manager.get_connection_stats()})
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"❌ WebSocket error in alerts: {e}")
                break
    finally:
        await websocket_manager.disconnect(websocket)


@router.get("/alerts/stats")
async def get_alerts_stats():
    """Get current WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()
