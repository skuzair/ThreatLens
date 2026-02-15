"""
dna_integration.py
───────────────────
Drop-in wrapper around DNAEngine that extracts the right features
from network and camera events, runs DNA profiling, and returns
an enriched event with dna_deviation_score attached.

Place this file in threatlens-data/processing/

Usage:
    from dna_integration import enrich_with_dna
    enriched_event = enrich_with_dna(event, source_type="network")
"""

import os
import sys
import logging

logger = logging.getLogger("dna-integration")

# ── Path setup ─────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

try:
    from dna_engine.infer import DNAEngine
    DNA_AVAILABLE = True
    logger.info("✅ DNA Engine loaded")
except Exception as e:
    DNA_AVAILABLE = False
    logger.warning(f"⚠️  DNA Engine not available: {e} — scores will be 0.0")

# ── Single shared engine instance (one Redis connection) ───────────────────
_engine = DNAEngine() if DNA_AVAILABLE else None


def _extract_network_features(event: dict) -> tuple[str, str, dict]:
    """
    Pull entity ID and relevant behavioral features from a network event.
    Returns (entity_type, entity_id, features_dict)
    """
    raw = event.get("raw_data", {})

    entity_id   = raw.get("source_ip", event.get("host", "unknown"))
    entity_type = "device"

    features = {
        "bytes_sent":      float(raw.get("bytes_sent", 0) or 0),
        "bytes_received":  float(raw.get("bytes_received", 0) or 0),
        "duration":        float(raw.get("duration_seconds", 0) or 0),
        "dest_port":       float(raw.get("dest_port", raw.get("dst_port", 0)) or 0),
        "hour_of_day":     float(_get_hour(event)),
    }

    return entity_type, entity_id, features


def _extract_camera_features(event: dict) -> tuple[str, str, dict]:
    """
    Pull entity ID and relevant behavioral features from a camera event.
    Returns (entity_type, entity_id, features_dict)
    """
    camera_id   = event.get("camera_id", event.get("host", "unknown"))
    entity_type = "camera"

    features = {
        "person_count":  float(event.get("person_count", event.get("detections", 0)) or 0),
        "anomaly_score": float(event.get("anomaly_score", 0) or 0),
        "hour_of_day":   float(_get_hour(event)),
    }

    return entity_type, camera_id, features


def _extract_log_features(event: dict) -> tuple[str, str, dict]:
    """
    Pull entity ID and features from a log event.
    Returns (entity_type, entity_id, features_dict)
    """
    raw         = event.get("raw_data", {})
    entity_id   = raw.get("user", raw.get("host", event.get("host", "unknown")))
    entity_type = "user"

    # Map event types to numeric risk values
    event_type_risk = {
        "login_success": 0,
        "login_failure": 1,
        "sudo":          2,
        "root_login":    3,
        "ssh_new_key":   2,
    }
    event_type    = raw.get("event_type", "unknown")
    event_risk    = float(event_type_risk.get(event_type, 0))

    features = {
        "event_risk":    event_risk,
        "hour_of_day":   float(_get_hour(event)),
        "pid":           float(raw.get("pid", 0) or 0),
    }

    return entity_type, entity_id, features


def _get_hour(event: dict) -> int:
    """Extract hour of day from event timestamp."""
    from datetime import datetime, timezone
    try:
        ts  = event.get("timestamp", "")
        dt  = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.hour
    except Exception:
        return datetime.now(timezone.utc).hour


def enrich_with_dna(event: dict, source_type: str) -> dict:
    """
    Main integration function. Call this from any detector.

    Args:
        event:       The raw or partially-scored event dict
        source_type: One of "network", "camera", "logs"

    Returns:
        The same event dict with these fields added/updated:
            - dna_deviation_score  (float 0-100)
            - dna_details          (dict with sigma, anomalous_metrics)
            - dna_entity_id        (which entity was profiled)
    """

    if not DNA_AVAILABLE or _engine is None:
        event["dna_deviation_score"] = 0.0
        event["dna_details"]         = {}
        return event

    try:
        # ── Extract features based on source type ──────────────────────────
        if source_type == "network":
            entity_type, entity_id, features = _extract_network_features(event)
        elif source_type == "camera":
            entity_type, entity_id, features = _extract_camera_features(event)
        elif source_type == "logs":
            entity_type, entity_id, features = _extract_log_features(event)
        else:
            logger.warning(f"Unknown source_type: {source_type}")
            event["dna_deviation_score"] = 0.0
            return event

        # ── Run DNA engine ─────────────────────────────────────────────────
        result = _engine.process_event(entity_type, entity_id, features)
        dna    = result.get("dna", {})

        # ── Attach DNA results to event ────────────────────────────────────
        event["dna_deviation_score"] = dna.get("overall_dna_deviation_score", 0.0)
        event["dna_details"]         = {
            "entity_id":        entity_id,
            "entity_type":      entity_type,
            "deviation_sigma":  dna.get("deviation_sigma", 0.0),
            "anomalous_metrics": dna.get("anomalous_metrics", []),
        }

        # Log if DNA deviation is significant
        dna_score = event["dna_deviation_score"]
        if dna_score > 50:
            logger.warning(
                f"🧬 High DNA deviation | Entity: {entity_id} | "
                f"Score: {dna_score:.1f} | "
                f"Anomalous: {[m['metric'] for m in dna.get('anomalous_metrics', [])]}"
            )

    except Exception as e:
        logger.error(f"DNA enrichment error: {e}")
        event["dna_deviation_score"] = 0.0
        event["dna_details"]         = {}

    return event