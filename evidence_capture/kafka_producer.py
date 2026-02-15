"""
Kafka Producer for Evidence Manifests - Fixed Version

Makes Kafka optional for local testing.
"""

import os
import json
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
ENABLE_KAFKA = os.getenv("ENABLE_KAFKA", "true").lower() == "true"

producer = None


def get_producer():
    """Get Kafka producer (returns None if Kafka disabled or unavailable)"""
    global producer
    
    if not ENABLE_KAFKA:
        print("[Evidence] Kafka disabled - skipping publish")
        return None
    
    if producer:
        return producer

    retries = 3  # Reduced retries for faster failure
    for i in range(retries):
        try:
            print(f"[Evidence] Connecting to Kafka (attempt {i+1}/{retries})...")
            producer = KafkaProducer(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                request_timeout_ms=5000,
                api_version_auto_timeout_ms=5000
            )
            print("[Evidence] ✓ Connected to Kafka")
            return producer
        except (NoBrokersAvailable, Exception) as e:
            if i < retries - 1:
                print(f"[Evidence] Kafka not ready, retrying...")
            else:
                print(f"[Evidence] ⚠️  Kafka unavailable - continuing without publish")
                return None

    return None


def publish_manifest(manifest):
    """
    Publish evidence manifest to Kafka.
    If Kafka is unavailable, saves to local file instead.
    """
    
    p = get_producer()
    
    if p:
        # Kafka available - publish
        try:
            p.send("evidence-manifest", manifest)
            p.flush()
            print(f"[Evidence] ✓ Published manifest to Kafka topic: evidence-manifest")
        except Exception as e:
            print(f"[Evidence] ⚠️  Failed to publish to Kafka: {e}")
            save_manifest_locally(manifest)
    else:
        # Kafka unavailable - save locally
        save_manifest_locally(manifest)


def save_manifest_locally(manifest):
    """Save manifest to local file when Kafka is unavailable"""
    
    incident_id = manifest.get("incident_id", "unknown")
    manifest_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "evidence",
        incident_id
    )
    
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, "manifest.json")
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"[Evidence] ✓ Saved manifest locally: {manifest_path}")