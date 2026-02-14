from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from api.websockets.manager import websocket_manager

router = APIRouter()


@router.websocket("/live/{source}")
async def live_data_websocket(websocket: WebSocket, source: str):
    """
    WebSocket endpoint for live monitoring data
    Sources: network, camera, rf, logs, files
    """
    if source not in ["network", "camera", "rf", "logs", "files"]:
        await websocket.close(code=1003, reason="Invalid source")
        return
    
    await websocket_manager.connect_live(websocket, source)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "source": source
                    })
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"❌ WebSocket error in live:{source}: {e}")
                break
    finally:
        await websocket_manager.disconnect(websocket)
