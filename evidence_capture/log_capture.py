import os
import json
from datetime import datetime


async def capture_logs(incident, base_folder):

    logs_folder = os.path.join(base_folder, "logs")
    os.makedirs(logs_folder, exist_ok=True)

    timestamp_range = incident.get("timestamp_range", {})

    mock_logs = {
        "zone": incident.get("zone"),
        "timestamp_range": timestamp_range,
        "events": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "User login attempt failed",
                "severity": "medium"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Unauthorized file access attempt",
                "severity": "high"
            }
        ]
    }

    snippet_path = os.path.join(logs_folder, "log_snippet.json")

    with open(snippet_path, "w") as f:
        json.dump(mock_logs, f, indent=4)

    return {
        "log_snippet_path": snippet_path,
        "event_count": len(mock_logs["events"]),
        "time_range": timestamp_range
    }
