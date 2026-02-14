# save as test_camera.py in camera_service folder
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

def send_frame(image_path, zone="server_room", hour_override=None):
    # Read image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Could not read image: {image_path}")
        return

    # Encode to base64
    _, buffer = cv2.imencode(".jpg", frame)
    frame_b64 = base64.b64encode(buffer).decode("utf-8")

    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_type": "camera",
        "host": "CAM_SERVER_ROOM_01",
        "camera_id": "CAM_SERVER_ROOM_01",
        "zone": zone,
        "raw_data": {
            "frame_base64": frame_b64,
            "camera_id": "CAM_SERVER_ROOM_01",
            "zone": zone,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    producer.send("raw-camera-frames", event)
    producer.flush()
    print(f"Sent frame from {image_path} — zone: {zone}")

# Send your test image
send_frame("test.png", zone="server_room")

producer.close()
print("Done — check main.py terminal for detection output")