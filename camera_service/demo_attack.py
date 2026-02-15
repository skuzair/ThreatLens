"""
demo_attack.py
──────────────
Demo script for ThreatLens camera detection.
Simulates a physical security incident:

1. Sends a NORMAL frame (empty room)         -> LOW score
2. Sends an INTRUDER frame (person detected) -> HIGH score
3. Sends AFTER HOURS INTRUDER frame          -> CRITICAL score

Run from ThreatLens root:
    python camera_service/demo_attack.py
    python camera_service/demo_attack.py --use-webcam
    python camera_service/demo_attack.py --image "path/to/photo.jpg"
"""

import cv2
import base64
import json
import uuid
import time
import argparse
import numpy as np
from datetime import datetime, timezone
from kafka import KafkaProducer

KAFKA_BROKER = "localhost:9092"
TOPIC        = "raw-camera-frames"


def encode_frame(frame):
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode("utf-8")


def make_event(frame, zone, camera_id):
    return {
        "event_id":   str(uuid.uuid4()),
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "source_type": "camera",
        "host":       camera_id,
        "camera_id":  camera_id,
        "zone":       zone,
        "raw_data": {
            "camera_id":    camera_id,
            "frame_base64": encode_frame(frame),
            "resolution":   "1280x720",
            "fps":          5
        },
        "anomaly_score":       0.0,
        "severity":            "low",
        "dna_deviation_score": 0.0
    }


def create_empty_room_frame():
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[:] = (40, 40, 40)
    for x in [80, 260, 440, 620, 800, 980]:
        cv2.rectangle(frame, (x, 150), (x + 140, 620), (20, 20, 80), -1)
        cv2.rectangle(frame, (x, 150), (x + 140, 620), (50, 50, 120), 2)
        for y in range(180, 600, 25):
            color = (0, 220, 0) if y % 50 == 0 else (0, 80, 0)
            cv2.circle(frame, (x + 15, y), 4, color, -1)
    cv2.rectangle(frame, (0, 630), (1280, 720), (30, 30, 30), -1)
    cv2.line(frame, (0, 630), (1280, 630), (70, 70, 70), 2)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, "CAM_SERVER_ROOM_01", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    cv2.putText(frame, ts, (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)
    cv2.putText(frame, "ZONE: SERVER ROOM A", (10, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)
    cv2.putText(frame, "NO MOTION DETECTED", (900, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    return frame


def add_alert_overlay(frame, after_hours=False):
    frame = frame.copy()
    cv2.rectangle(frame, (0, 0), (1279, 719), (0, 0, 220), 8)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, "CAM_SERVER_ROOM_01", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, ts, (10, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    if after_hours:
        cv2.rectangle(frame, (380, 40), (1050, 105), (0, 0, 180), -1)
        cv2.putText(frame, "AFTER HOURS ACCESS DETECTED", (390, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        cv2.putText(frame, "NO BADGE SCAN RECORDED", (390, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 50, 255), 1)
    cv2.putText(frame, "!! MOTION DETECTED !!", (880, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    return frame


def capture_webcam_frame():
    print("\n   Opening webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("   Could not open webcam")
        return None
    for _ in range(15):
        cap.read()
    print("   Capturing in:")
    for i in range(3, 0, -1):
        print(f"      {i}...")
        time.sleep(1)
    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        return None
    frame = cv2.resize(frame, (1280, 720))
    print("   Webcam frame captured")
    return frame


def get_intruder_frame(use_webcam, image_path):
    if image_path:
        frame = cv2.imread(image_path)
        if frame is not None:
            print(f"   Using image: {image_path}")
            return cv2.resize(frame, (1280, 720))

    if use_webcam:
        frame = capture_webcam_frame()
        if frame is not None:
            return frame

    for path in ["test.png", "camera_service/test.png"]:
        frame = cv2.imread(path)
        if frame is not None:
            print(f"   Using: {path}")
            return cv2.resize(frame, (1280, 720))

    print("   Using synthetic person silhouette")
    frame = create_empty_room_frame()
    cx = 640
    cv2.circle(frame, (cx, 200), 55, (160, 130, 110), -1)
    cv2.rectangle(frame, (cx - 55, 255), (cx + 55, 480), (80, 60, 120), -1)
    cv2.rectangle(frame, (cx - 50, 480), (cx - 10, 640), (60, 45, 90), -1)
    cv2.rectangle(frame, (cx + 10, 480), (cx + 50, 640), (60, 45, 90), -1)
    cv2.rectangle(frame, (cx - 100, 260), (cx - 55, 440), (80, 60, 120), -1)
    cv2.rectangle(frame, (cx + 55, 260), (cx + 100, 440), (80, 60, 120), -1)
    return frame


def run_demo(use_webcam=False, image_path=None):
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        max_request_size=10485760
    )

    print("\n" + "=" * 60)
    print("   ThreatLens AI - Camera Detection Demo")
    print("=" * 60)

    print("\n[1/3] Sending NORMAL frame (empty server room)...")
    event1 = make_event(create_empty_room_frame(), "server_room", "CAM_SERVER_ROOM_01")
    producer.send(TOPIC, event1)
    producer.flush()
    print("      Sent - expect: LOW score (0-20)")
    time.sleep(3)

    print("\n[2/3] Preparing INTRUDER frame...")
    intruder = get_intruder_frame(use_webcam, image_path)
    intruder = add_alert_overlay(intruder, after_hours=False)
    event2 = make_event(intruder, "server_room", "CAM_SERVER_ROOM_01")
    producer.send(TOPIC, event2)
    producer.flush()
    print("      Sent - expect: HIGH score (25-75)")
    time.sleep(3)

    print("\n[3/3] Sending AFTER-HOURS INTRUDER frame...")
    dark = (intruder.copy() * 0.35).astype(np.uint8)
    dark = add_alert_overlay(dark, after_hours=True)
    event3 = make_event(dark, "server_room", "CAM_SERVER_ROOM_01")
    producer.send(TOPIC, event3)
    producer.flush()
    print("      Sent - expect: CRITICAL score (75+)")

    print("\n" + "=" * 60)
    print("   Demo complete! Check camera detector terminal.")
    print("   Expected:")
    print("   Frame #0001 | LOW      | Score:   0.0 | Persons: 0")
    print("   Frame #0002 | HIGH     | Score:  50.0 | Persons: 2")
    print("   Frame #0003 | CRITICAL | Score: 100.0 | Persons: 4")
    print("=" * 60 + "\n")

    producer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ThreatLens Camera Demo")
    parser.add_argument("--use-webcam", action="store_true")
    parser.add_argument("--image", type=str, default=None)
    args = parser.parse_args()
    run_demo(use_webcam=args.use_webcam, image_path=args.image)