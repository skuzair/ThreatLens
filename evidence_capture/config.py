"""
Evidence Capture Configuration - Fixed for Windows
"""

import os
from pathlib import Path

# Kafka connection
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Elasticsearch (if needed)
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")

# Evidence storage root - use absolute Windows path
# Default: C:\Users\Samagra\Documents\ThreatLens\evidence
EVIDENCE_ROOT = os.getenv(
    "EVIDENCE_ROOT",
    str(Path(__file__).parent.parent / "evidence")
)

# Create evidence root if it doesn't exist
os.makedirs(EVIDENCE_ROOT, exist_ok=True)

print(f"[Config] Evidence will be stored at: {EVIDENCE_ROOT}")