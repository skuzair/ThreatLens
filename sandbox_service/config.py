"""
Sandbox Service Configuration
All paths are absolute, derived from this file's location.
"""

from pathlib import Path
import os

# Absolute root of sandbox_service/
SERVICE_ROOT = Path(__file__).resolve().parent

# Evidence output root  →  sandbox_service/evidence/
EVIDENCE_ROOT = SERVICE_ROOT / "evidence"
EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)

# Kafka (optional — set ENABLE_KAFKA=false to skip)
BOOTSTRAP_SERVERS  = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
ENABLE_KAFKA       = os.getenv("ENABLE_KAFKA", "true").lower() == "true"

SANDBOX_TOPIC_IN   = "sandbox-requests"
SANDBOX_TOPIC_OUT  = "sandbox-results"

# Docker / execution
DETONATION_DURATION   = 120    # seconds (real container runtime cap)
SCREENSHOT_INTERVAL   = 2      # seconds between simulated frames
NUM_FRAMES            = 30     # frames to generate per detonation