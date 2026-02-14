# save as send_test_image.py inside camera_service folder
import cv2
import base64
import json
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

frame = cv2.imread("test.png")
_, buffer = cv2.imencode(".jpg", frame)
frame_b64 = base64.b64encode(buffer).decode("utf-8")

event = {
    "event_id": str(uuid.uuid4()),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "source_type": "camera",
    "host": "CAM_SERVER_ROOM_01",
    "camera_id": "CAM_SERVER_ROOM_01",
    "zone": "server_room",
    "raw_data": {
        "camera_id": "CAM_SERVER_ROOM_01",
        "frame_base64": frame_b64,
        "resolution": "1280x720",
        "fps": 5
    },
    "anomaly_score": 0.0,
    "severity": "low",
    "dna_deviation_score": 0.0
}

producer.send("raw-camera-frames", event)
producer.flush()
producer.close()
print("Sent test.png — check detector terminal")