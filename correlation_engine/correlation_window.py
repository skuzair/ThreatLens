"""
Correlation Window Manager

Responsibilities:
- Maintain sliding time windows of anomaly events
- Group events by zone
- Enforce anomaly score threshold
- Expire old events
- Return correlation-ready windows

This module is stateful and should be instantiated once
inside correlation_engine/infer.py
"""

from datetime import datetime, timedelta
from collections import defaultdict
import threading


class CorrelationWindowManager:

    def __init__(self,
                 window_size_minutes: int = 15,
                 anomaly_threshold: int = 40):
        """
        Args:
            window_size_minutes: Sliding window duration
            anomaly_threshold: Minimum anomaly score to include
        """

        self.window_size = timedelta(minutes=window_size_minutes)
        self.anomaly_threshold = anomaly_threshold

        # zone -> list of events
        self.events_by_zone = defaultdict(list)

        self.lock = threading.Lock()

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def add_event(self, event: dict):
        """
        Add anomaly event into window if above threshold.

        Expected event format:
        {
            "event_id": "...",
            "source": "network/logs/file/camera/rf",
            "score": 87,
            "zone": "server_room",
            "timestamp": "2024-01-15T02:04:23.000Z",
            ...
        }
        """

        if event.get("score", 0) < self.anomaly_threshold:
            return

        zone = event.get("zone", "global")

        parsed_time = self._parse_timestamp(event["timestamp"])
        event["_parsed_timestamp"] = parsed_time

        with self.lock:
            self.events_by_zone[zone].append(event)
            self._expire_old_events(zone)

    def get_active_windows(self):
        """
        Returns:
            List of window dictionaries ready for rule engine.

        Each window format:
        {
            "zone": "...",
            "window_start": datetime,
            "window_end": datetime,
            "events": [...]
        }
        """

        windows = []

        with self.lock:
            now = datetime.utcnow()

            for zone, events in self.events_by_zone.items():

                if not events:
                    continue

                window_start = now - self.window_size

                valid_events = [
                    e for e in events
                    if e["_parsed_timestamp"] >= window_start
                ]

                if not valid_events:
                    continue

                windows.append({
                    "zone": zone,
                    "window_start": window_start,
                    "window_end": now,
                    "events": valid_events
                })

        return windows

    def clear_zone(self, zone: str):
        """Clear events for a specific zone after incident creation."""
        with self.lock:
            self.events_by_zone[zone] = []

    # --------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------

    def _expire_old_events(self, zone: str):
        """Remove expired events beyond window size."""
        now = datetime.utcnow()
        cutoff = now - self.window_size

        self.events_by_zone[zone] = [
            e for e in self.events_by_zone[zone]
            if e["_parsed_timestamp"] >= cutoff
        ]

    @staticmethod
    def _parse_timestamp(ts: str) -> datetime:
        """
        Parse ISO timestamp safely.
        """
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            # fallback to current time if parsing fails
            return datetime.utcnow()
