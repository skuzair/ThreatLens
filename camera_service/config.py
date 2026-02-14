import os

# ========================
# KAFKA CONFIG
# ========================
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
RAW_CAMERA_FRAMES_TOPIC = "raw-camera-frames"
CAMERA_ANOMALY_SCORES_TOPIC = "camera-anomaly-scores"


# ========================
# MODEL CONFIG
# ========================
YOLO_MODEL_PATH = "yolov8n.pt"
MIN_CONFIDENCE = 0.4

# ========================
# EVIDENCE CONFIG
# ========================
EVIDENCE_DIR = "evidence"

# ========================
# SCORING WEIGHTS
# ========================
SCORE_WEIGHTS = {
    "no_badge_scan": 40,
    "after_hours": 30,
    "loitering": 20,
    "restricted_zone": 30
}

CONFIDENCE_THRESHOLD = 0.90
CONFIDENCE_MULTIPLIER = 1.1

# ========================
# ZONE DEFINITIONS
# ========================
ZONES = {
    "server_room": {
        "polygon": [(0,0), (1280,0), (1280,720), (0,720)],
        "permitted_hours": (8, 18),
        "max_persons": 2,
        "requires_badge": True
    },
    "lobby": {
        "polygon": [(0,0), (1280,0), (1280,400), (0,400)],
        "permitted_hours": (6, 22),
        "max_persons": 50,
        "requires_badge": False
    }
}
