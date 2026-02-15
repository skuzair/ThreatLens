import asyncio
from orchestrator import process_incident

fake_incident = {
    "incident_id": "INC-LOCAL-001",
    "correlated_events": [],
    "timestamp_range": {
        "start": "2024-01-15T02:03:00Z",
        "end": "2024-01-15T02:07:30Z"
    },
    "sources_involved": ["camera", "logs", "network", "file"],
    "zone": "server_room"
}

if __name__ == "__main__":
    asyncio.run(process_incident(fake_incident))
