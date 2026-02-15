"""
file_detector.py
─────────────────
Consumes raw file events from Kafka topic `raw-file-events`,
runs Isolation Forest anomaly detection + DNA enrichment,
publishes scored events to `file-anomaly-scores`.

Place in: threatlens-data/processing/file_detector.py
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

# ── Path setup ─────────────────────────────────────────────────────────────
# processing/ → threatlens-data/ → ThreatLens/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from kafka import KafkaConsumer, KafkaProducer
from file_model.infer import FileAnomalyPredictor
from dna_integration import enrich_with_dna

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("file-detector")

# ── Kafka config ───────────────────────────────────────────────────────────
KAFKA_BROKER  = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
INPUT_TOPIC   = "raw-file-events"
OUTPUT_TOPIC  = "file-anomaly-scores"

# ── Load model ─────────────────────────────────────────────────────────────
logger.info("Loading file anomaly model...")
try:
    predictor = FileAnomalyPredictor()
    logger.info("✅ File model loaded")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    logger.error("Run: python file_model/train_isolation_forest.py")
    sys.exit(1)

# ── Kafka connections ──────────────────────────────────────────────────────
consumer = KafkaConsumer(
    INPUT_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    group_id="file-detector-group",
    auto_offset_reset="latest",
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def severity_from_score(score: float) -> str:
    if score >= 80:   return "critical"
    elif score >= 60: return "high"
    elif score >= 40: return "medium"
    else:             return "low"


def extract_features(event: dict) -> list:
    """
    Pull file activity features from event.
    Handles both direct fields and nested raw_data.
    """
    raw  = event.get("raw_data", {})
    if not raw:
        raw = event

    hour = datetime.now(timezone.utc).hour
    try:
        ts   = event.get("timestamp", "")
        from datetime import datetime as dt
        hour = dt.fromisoformat(ts.replace("Z", "+00:00")).hour
    except Exception:
        pass

    return [
        float(raw.get("modifications_per_minute",  0) or 0),
        float(raw.get("unique_processes_writing",  1) or 1),
        float(raw.get("extension_change_rate",     0) or 0),
        float(raw.get("file_size_change_ratio",    1.0) or 1.0),
        float(raw.get("sensitive_dir_access_rate", 0) or 0),
        float(hour),
    ]


def process_event(event: dict) -> dict | None:
    raw = event.get("raw_data", {})
    if not raw:
        raw = event

    try:
        features = extract_features(event)
        result   = predictor.predict(features)
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return None

    anomaly_score = result["anomaly_score"]
    is_anomaly    = result["is_anomaly"]

    output = {
        "event_id":            event.get("event_id", "unknown"),
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "source_type":         "file",
        "host":                event.get("host", raw.get("host", "unknown")),
        "zone":                event.get("zone", "internal"),
        "raw_data":            raw,
        "anomaly_score":       anomaly_score,
        "is_anomaly":          is_anomaly,
        "severity":            severity_from_score(anomaly_score),
        "dna_deviation_score": 0.0,
        "feature_vector":      features,
        "triggered_rules":     _check_rules(raw),
    }

    return output


def _check_rules(raw: dict) -> list:
    """Quick rule checks for obvious ransomware patterns."""
    rules = []
    mpm = float(raw.get("modifications_per_minute", 0) or 0)
    ecr = float(raw.get("extension_change_rate",    0) or 0)
    sda = float(raw.get("sensitive_dir_access_rate",0) or 0)

    if mpm > 50:   rules.append("mass_modification")
    if ecr > 0.5:  rules.append("bulk_extension_change")
    if sda > 0.4:  rules.append("sensitive_dir_access")
    if mpm > 100 and ecr > 0.6:
        rules.append("ransomware_pattern")

    return rules


def run():
    logger.info(f"🚀 File Detector started — [{INPUT_TOPIC}] → [{OUTPUT_TOPIC}]")
    logger.info("Waiting for events...")

    event_count = 0

    try:
        for msg in consumer:
            try:
                event        = msg.value
                event_count += 1

                output = process_event(event)
                if output is None:
                    continue

                # DNA enrichment
                output = enrich_with_dna(output, source_type="file")

                producer.send(OUTPUT_TOPIC, output)
                producer.flush()

                score     = output["anomaly_score"]
                dna       = output.get("dna_deviation_score", 0.0)
                severity  = output["severity"].upper()
                rules     = output.get("triggered_rules", [])
                host      = output["host"]

                if score >= 80:   indicator = "🔴 CRITICAL"
                elif score >= 60: indicator = "🟠 HIGH    "
                elif score >= 40: indicator = "🟡 MEDIUM  "
                else:             indicator = "🟢 LOW     "

                rule_str = f" | Rules: {rules}" if rules else ""

                logger.info(
                    f"Event #{event_count:04d} | {indicator} | "
                    f"Score: {score:5.1f} | DNA: {dna:5.1f} | "
                    f"Host: {host}{rule_str}"
                )

            except Exception as e:
                logger.exception(f"Error: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("🛑 File detector stopped")
    finally:
        consumer.close()
        producer.close()
        logger.info(f"✅ Processed {event_count} events")


if __name__ == "__main__":
    run()