from collections import defaultdict
import time

entry_time = defaultdict(lambda: time.time())

def check_violations(track_id, zone_name, zone_config, timestamp):
    violations = []

    if zone_config["requires_badge"]:
        badge_recorded = False
        if not badge_recorded:
            violations.append("no_badge_scan")

    hour = int(timestamp[11:13])
    if not zone_config["permitted_hours"][0] <= hour <= zone_config["permitted_hours"][1]:
        violations.append("after_hours")

    duration = (time.time() - entry_time[track_id]) / 60
    if duration > 5:
        violations.append("loitering")

    return violations, duration
