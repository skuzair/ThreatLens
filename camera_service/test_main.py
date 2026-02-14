"""Quick test for process_event. Run from camera_service: python test_main.py"""
from main import process_event
import json

# Minimal 1x1 PNG as base64 (so process_event can decode and run detection)
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAChwGA60e6kgAAAABJRU5ErkJggg=="

event = {
    "event_id": "cam-test-001",
    "host": "cam-001",
    "zone": "lobby",
    "raw_data": {
        "frame_base64": TINY_PNG_B64,
    },
    "timestamp": "2024-01-15T02:03:12",
}

result = process_event(event)
print(json.dumps(result, indent=4))
