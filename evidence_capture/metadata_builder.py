import json
from datetime import datetime

def create_metadata(incident, folder):
    metadata = {
        "incident_id": incident["incident_id"],
        "risk_score": incident["risk_score"],
        "severity": incident["severity"],
        "intent": incident.get("intent", {}).get("primary"),
        "sources": incident.get("sources_involved", []),
        "generated_at": datetime.utcnow().isoformat()
    }

    with open(f"{folder}/metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata
