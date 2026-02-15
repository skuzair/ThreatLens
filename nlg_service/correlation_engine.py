from datetime import datetime


class CorrelationEngine:

    def _parse_time(self, timestamp: str):
        """
        Accept HH:MM  or  full ISO-8601 strings
        (e.g. "02:03"  or  "2026-02-15T14:23:00Z").
        Returns a datetime (date part is ignored for window calc).
        """
        if not timestamp:
            return None

        # Try short HH:MM first
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(timestamp, fmt)
            except ValueError:
                pass

        # Try ISO variants
        for fmt in (
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(timestamp, fmt)
            except ValueError:
                pass

        return None

    def calculate_window(self, events: list) -> int:
        """Return the event window in minutes (0 if < 2 parseable timestamps)."""
        times = []
        for e in events:
            ts = e.get("timestamp") if isinstance(e, dict) else None
            parsed = self._parse_time(ts)
            if parsed:
                times.append(parsed)

        if len(times) < 2:
            return 0

        delta = max(times) - min(times)
        return int(delta.seconds / 60)

    def build_sequence(self, incident: dict) -> str:
        mapping = {
            "camera_event":  "physical entry",
            "logs_event":    "login",
            "file_event":    "file encryption",
            "network_event": "exfiltration",
        }

        events = []
        for key, label in mapping.items():
            if key in incident:
                ts = incident[key].get("timestamp")
                if ts:
                    events.append((ts, label))

        if not events:
            return "unknown sequence"

        events_sorted = sorted(events, key=lambda x: x[0])
        return " → ".join(e[1] for e in events_sorted)

    def infer_attack_pattern(self, intent: str) -> str:
        patterns = {
            "DATA_EXFILTRATION": "insider data theft",
            "data_exfiltration": "insider data theft",
            "RANSOMWARE":        "ransomware impact",
            "ransomware":        "ransomware impact",
        }
        return patterns.get(intent, "multi-stage intrusion")