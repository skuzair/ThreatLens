"""
Rule Engine - Evaluates correlation rules against event windows
"""

from datetime import datetime, timedelta
from collections import defaultdict
from .rules_config import CORRELATION_RULES


class RuleEngine:

    def __init__(self):
        self.rules = CORRELATION_RULES

    def evaluate(self, window):
        """
        Evaluate rules against a time window of events
        
        window format:
        {
            "zone": "...",
            "window_start": datetime,
            "window_end": datetime,
            "events": [...]
        }
        
        Returns:
            tuple: (matched_rule, filtered_events) or (None, None)
        """
        events = window["events"]
        zone = window["zone"]

        for rule in self.rules:
            matched, filtered_events = self._check_rule(rule, events, zone)
            if matched:
                return rule, filtered_events

        return None, None

    def _check_rule(self, rule, events, zone):
        """Check if a rule matches the given events"""
        
        required = rule.get("required_sources", [])
        optional = rule.get("optional_sources", [])
        min_scores = rule.get("min_scores", {})
        window_minutes = rule.get("time_window_minutes", 10)
        zone_required = rule.get("zone_match_required", False)
        ransomware_required = rule.get("ransomware_pattern_required", False)

        # Group events by source
        source_groups = defaultdict(list)
        for e in events:
            source_groups[e["source"]].append(e)

        # 1. Required sources present
        for src in required:
            if src not in source_groups:
                return False, None

        # 2. Minimum score validation
        for src, min_score in min_scores.items():
            if src in source_groups:
                if not any(e["score"] >= min_score for e in source_groups[src]):
                    return False, None

        # 3. Ransomware flag validation
        if ransomware_required:
            file_events = source_groups.get("file", [])
            if not any(e.get("ransomware_pattern", False) for e in file_events):
                return False, None

        # 4. Zone matching
        if zone_required:
            zones = set(e.get("zone") for e in events)
            if len(zones) > 1:
                return False, None

        # 5. Time window constraint
        timestamps = []
        for e in events:
            try:
                timestamps.append(datetime.fromisoformat(e["timestamp"]))
            except Exception:
                return False, None

        if timestamps:
            if max(timestamps) - min(timestamps) > timedelta(minutes=window_minutes):
                return False, None

        # 6. Build filtered set (only relevant sources)
        relevant_sources = set(required + optional)
        filtered = [
            e for e in events
            if e["source"] in relevant_sources
        ]

        return True, filtered