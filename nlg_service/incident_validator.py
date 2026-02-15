class IncidentValidator:

    REQUIRED_FIELDS = ["incident_id", "risk_score", "severity", "intent"]

    # At least one of these event types must be present
    EVENT_FIELDS = ["camera_event", "logs_event", "file_event", "network_event"]

    def validate(self, incident: dict):
        missing = [f for f in self.REQUIRED_FIELDS if f not in incident]
        if missing:
            return False, missing

        has_event = any(f in incident for f in self.EVENT_FIELDS)
        if not has_event:
            return False, ["At least one of: " + ", ".join(self.EVENT_FIELDS)]

        return True, []