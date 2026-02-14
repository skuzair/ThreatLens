from consumers.base_consumer import BaseConsumer
from api.websockets.manager import websocket_manager
from datetime import datetime


class LiveConsumer(BaseConsumer):
    """Consumes live monitoring data and broadcasts to WebSocket clients"""
    
    def __init__(self):
        super().__init__(
            topics=[
                "network-anomalies",
                "camera-alerts",
                "rf-anomalies",
                "log-anomalies",
                "file-events"
            ],
            group_id="live-monitor"
        )
    
    async def handle_message(self, topic: str, data: dict):
        """Route live data to appropriate WebSocket channel"""
        try:
            # Map topic to source name
            source_map = {
                "network-anomalies": "network",
                "camera-alerts": "camera",
                "rf-anomalies": "rf",
                "log-anomalies": "logs",
                "file-events": "files"
            }
            
            source = source_map.get(topic)
            if source:
                # Broadcast to live monitoring WebSocket clients
                await websocket_manager.broadcast_to_live(source, {
                    "type": "live_update",
                    "source": source,
                    "timestamp": data.get("timestamp", datetime.now().isoformat()),
                    "data": data
                })
                
                # Also update main alert feed if anomaly score is high
                if data.get("anomaly_score", 0) > 75:
                    await websocket_manager.broadcast_to_alerts({
                        "type": "high_anomaly",
                        "source": source,
                        "data": data
                    })
            
        except Exception as e:
            print(f"❌ Error in LiveConsumer.handle_message for {topic}: {e}")
