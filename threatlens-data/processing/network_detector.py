"""
network_detector.py
────────────────────
Consumes raw network events from Kafka topic `raw-network-events`,
extracts features, runs Isolation Forest + Autoencoder ensemble,
and produces anomaly scores to `network-anomaly-scores`.

Uses kafka-python (not confluent-kafka).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

# ── Path setup ─────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from network_model.infer import NetworkInference
from network_model.preprocess_unsw import preprocess_single_event
from dna_integration import enrich_with_dna

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("network-detector")

# ── Kafka config ───────────────────────────────────────────────────────────
KAFKA_BROKER  = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INPUT_TOPIC   = "raw-network-events"
OUTPUT_TOPIC  = "network-anomaly-scores"

# ── Load model once at startup ─────────────────────────────────────────────
logger.info("Loading network inference models...")
try:
    inference_engine = NetworkInference()
    logger.info("✅ Models loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load models: {e}")
    sys.exit(1)

# ── Kafka consumer ─────────────────────────────────────────────────────────
consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    group_id="network-detector-group",
    auto_offset_reset="latest",
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

# ── Kafka producer ─────────────────────────────────────────────────────────
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def severity_from_score(score: float) -> str:
    if score >= 80:
        return "critical"
    elif score >= 60:
        return "high"
    elif score >= 40:
        return "medium"
    else:
        return "low"


def process_event(event: dict):
    # Guard: skip already-scored events
    if event.get("anomaly_score") is not None and event.get("source_type") != "network":
        logger.warning("Skipping already-scored event")
        return None

    # Extract raw_data
    raw = event.get("raw_data", {})
    if not raw:
        raw = event

    # Pull values
    duration       = float(raw.get("duration_seconds", 0) or 0)
    bytes_sent     = float(raw.get("bytes_sent", 0) or 0)
    bytes_received = float(raw.get("bytes_received", 0) or 0)
    dst_port       = int(raw.get("dest_port", raw.get("dst_port", 0)) or 0)

    # Derive features
    spkts  = max(1, int(bytes_sent / 512))
    dpkts  = max(1, int(bytes_received / 512))
    sload  = bytes_sent     / (duration + 1e-6)
    dload  = bytes_received / (duration + 1e-6)
    sttl   = 64 if dst_port < 1024 else 128
    sinpkt = duration / (spkts + 1)
    dinpkt = duration / (dpkts + 1)

    feature_vector = [
        duration, spkts, dpkts, bytes_sent, bytes_received,
        sttl, 64, sload, dload, 0, 0,
        sinpkt, dinpkt, 0, 0, 8192, 8192, 0, 0, 0
    ]

    non_zero = [(i, round(f, 3)) for i, f in enumerate(feature_vector) if f != 0]
    logger.info(f"Non-zero features: {non_zero}")

    try:
        anomaly_score = inference_engine.predict(feature_vector)
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return None

    return {
        "event_id":            event.get("event_id", "unknown"),
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "source_type":         "network",
        "host":                event.get("host", raw.get("source_ip", "unknown")),
        "zone":                event.get("zone", "internal"),
        "raw_data":            raw,
        "anomaly_score":       anomaly_score,
        "severity":            severity_from_score(anomaly_score),
        "dna_deviation_score": 0.0,  # will be set by enrich_with_dna below
        "feature_vector":      feature_vector,
    }


def run():
    logger.info(f"Network Detector started — [{INPUT_TOPIC}] → [{OUTPUT_TOPIC}]")
    try:
        for msg in consumer:
            try:
                event = msg.value
                logger.info(f"Received: {event.get('event_id', 'unknown')}")

                output = process_event(event)
                if output is None:
                    continue

                # ── DNA enrichment ─────────────────────────────────────────
                output = enrich_with_dna(output, source_type="network")

                producer.send(OUTPUT_TOPIC, output)
                producer.flush()

                dna_score = output.get("dna_deviation_score", 0.0)
                logger.info(
                    f"Score: {output['anomaly_score']:6.2f} | "
                    f"DNA: {dna_score:5.1f} | "
                    f"Severity: {output['severity']:8s} | "
                    f"Host: {output['host']} | "
                    f"Bytes up={output['raw_data'].get('bytes_sent',0)} "
                    f"down={output['raw_data'].get('bytes_received',0)}"
                )

            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("Detector stopped")
    finally:
        consumer.close()
        producer.close()
        logger.info("Kafka connections closed")


if __name__ == "__main__":
    run()