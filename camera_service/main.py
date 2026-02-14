"""
ThreatLens – Camera Detection Service
Consumes raw camera frames from Kafka, runs YOLOv8 detection,
publishes anomaly scores to camera-anomaly-scores topic.
"""

import json
import base64
import logging
import os
from datetime import datetime

import numpy as np
import cv2
from kafka import KafkaConsumer, KafkaProducer

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except Exception:
    YOLO_AVAILABLE = False

# ── Logging — clean format for demo ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("camera-detector")

# ── Kafka config ───────────────────────────────────────────────────────────
KAFKA_BROKER         = os.getenv("KAFKA_BROKER", "localhost:9092")
RAW_CAMERA_TOPIC     = "raw-camera-frames"
CAMERA_ANOMALY_TOPIC = "camera-anomaly-scores"
CONSUMER_GROUP       = "camera-detector-group"

# ── Load YOLO ──────────────────────────────────────────────────────────────
model = None
if YOLO_AVAILABLE:
    try:
        logger.info("Loading YOLOv8 model...")
        model = YOLO("yolov8n.pt")
        logger.info("✅ YOLOv8 loaded successfully")
    except Exception as e:
        logger.error(f"❌ YOLO load failed: {e}")
else:
    logger.warning("⚠️  YOLO not available — running in stub mode")


def process_event(event: dict) -> dict | None:
    """
    Process a single camera frame event.
    Returns scored output event or None if frame is invalid.
    """
    raw_data = event.get("raw_data", event)

    # ── Decode base64 frame ────────────────────────────────────────────────
    frame_base64 = raw_data.get("frame_base64")
    if not frame_base64:
        logger.warning("Skipping event — frame_base64 missing")
        return None

    try:
        frame_bytes = base64.b64decode(frame_base64)
        np_arr      = np.frombuffer(frame_bytes, np.uint8)
        frame       = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.warning(f"Frame decode failed: {e}")
        return None

    if frame is None or frame.size == 0:
        logger.warning("Skipping event — empty frame after decode")
        return None

    # ── Ensure correct format for YOLO ────────────────────────────────────
    if frame.dtype != np.uint8:
        frame = frame.astype(np.uint8)
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    # ── Run YOLO detection ─────────────────────────────────────────────────
    anomaly_score = 0.0
    severity      = "low"
    person_count  = 0

    if model:
        try:
            results = model(frame, verbose=False, classes=[0])  # class 0 = person only
            for r in results:
                if r.boxes is not None:
                    person_count = len(r.boxes)

            if person_count > 0:
                anomaly_score = min(100.0, person_count * 25.0)
                severity      = "high" if anomaly_score >= 60 else "medium"

        except Exception as e:
            logger.error(f"YOLO inference error: {e}")

    # ── Build output event ─────────────────────────────────────────────────
    zone          = event.get("zone", raw_data.get("zone", "unknown"))
    camera_id     = event.get("host", raw_data.get("camera_id", "unknown"))

    return {
        "event_id":      event.get("event_id"),
        "timestamp":     datetime.utcnow().isoformat(),
        "source_type":   "camera",
        "camera_id":     camera_id,
        "zone":          zone,
        "anomaly_score": anomaly_score,
        "severity":      severity,
        "person_count":  person_count,
    }


if __name__ == "__main__":

    consumer = KafkaConsumer(
        RAW_CAMERA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="latest",       # only process new frames
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    logger.info("🚀 Camera detection service started")
    logger.info(f"📡 Listening on [{RAW_CAMERA_TOPIC}]")
    logger.info(f"📤 Publishing to [{CAMERA_ANOMALY_TOPIC}]")
    logger.info("Waiting for frames...\n")

    frame_count = 0

    try:
        for msg in consumer:
            try:
                event        = msg.value
                frame_count += 1
                event_id     = event.get("event_id", "unknown")[:8]  # short ID for display
                zone         = event.get("zone", "unknown")

                output = process_event(event)

                if output is None:
                    logger.warning(f"Frame {frame_count} | Skipped — invalid frame")
                    continue

                producer.send(CAMERA_ANOMALY_TOPIC, output)
                producer.flush()

                # ── Clean demo output ──────────────────────────────────────
                score    = output["anomaly_score"]
                severity = output["severity"].upper()
                persons  = output["person_count"]

                # Severity indicator
                if score >= 80:
                    indicator = "🔴 CRITICAL"
                elif score >= 60:
                    indicator = "🟠 HIGH    "
                elif score >= 40:
                    indicator = "🟡 MEDIUM  "
                else:
                    indicator = "🟢 LOW     "

                logger.info(
                    f"Frame #{frame_count:04d} | "
                    f"{indicator} | "
                    f"Score: {score:5.1f}/100 | "
                    f"Persons: {persons} | "
                    f"Zone: {zone} | "
                    f"ID: {event_id}..."
                )

            except Exception as e:
                logger.exception(f"Error processing frame: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("\n🛑 Camera service stopped")
    finally:
        consumer.close()
        producer.close()
        logger.info(f"✅ Processed {frame_count} frames total")