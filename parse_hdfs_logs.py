"""
parse_hdfs_logs.py
───────────────────
Parses raw HDFS_2k.log file into feature vectors for training.

Place HDFS_2k.log in the log_model/ folder then run:
    python log_model/parse_hdfs_logs.py

Output: log_model/data/log_features.csv
"""

import re
import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent        # log_model/
LOG_PATH    = BASE_DIR / "HDFS_2k.log"
OUTPUT_DIR  = BASE_DIR / "data"
OUTPUT_PATH = OUTPUT_DIR / "log_features.csv"

# ── HDFS log line pattern ──────────────────────────────────────────────────
# Example line:
# 081109 203518 148 INFO dfs.DataNode$PacketResponder: Received block blk_-1608999687919862906 of size 67108864 from /10.251.43.115
LOG_PATTERN = re.compile(
    r'(\d{6})\s+'       # date e.g. 081109
    r'(\d{6})\s+'       # time e.g. 203518
    r'(\d+)\s+'         # pid
    r'(\w+)\s+'         # level INFO/WARN/ERROR
    r'([\w.$]+):\s+'    # component
    r'(.+)'             # content
)

# Keywords that indicate anomalous activity
ERROR_KEYWORDS   = ["Exception", "Error", "Failed", "Lost", "Unable", "Cannot"]
WARNING_KEYWORDS = ["Retry", "Timeout", "Slow", "Warning", "WARN"]
CRITICAL_KEYWORDS= ["corrupt", "missing", "unreachable", "IOException", "OutOfMemory"]


def parse_line(line):
    """Parse a single HDFS log line into a dict."""
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None
    date, time_str, pid, level, component, content = m.groups()
    return {
        "date":      date,
        "time":      time_str,
        "pid":       int(pid),
        "level":     level.upper(),
        "component": component,
        "content":   content,
    }


def extract_block_id(content):
    """Pull block ID from log content."""
    m = re.search(r'blk_[-\d]+', content)
    return m.group(0) if m else None


def get_hour(time_str):
    """Extract hour from HHMMSS string."""
    try:
        return int(time_str[:2])
    except Exception:
        return 12


def build_features(lines):
    """Build one feature vector from all log lines for a block."""
    n          = len(lines)
    levels     = [l["level"] for l in lines]
    contents   = [l["content"] for l in lines]
    hours      = [get_hour(l["time"]) for l in lines]
    components = set(l["component"] for l in lines)

    # Level encoding
    level_map  = {"INFO": 0, "WARN": 1, "WARNING": 1, "ERROR": 2, "FATAL": 3}
    level_nums = [level_map.get(lv, 0) for lv in levels]
    max_level  = max(level_nums) if level_nums else 0
    avg_level  = float(np.mean(level_nums)) if level_nums else 0

    # Error counting
    n_errors   = sum(1 for lv in levels if lv in ("ERROR", "FATAL"))
    n_warnings = sum(1 for lv in levels if lv in ("WARN", "WARNING"))
    error_rate = n_errors / max(n, 1)

    # Keyword scanning
    full_text  = " ".join(contents).lower()
    n_critical = sum(1 for kw in CRITICAL_KEYWORDS if kw.lower() in full_text)
    n_error_kw = sum(1 for kw in ERROR_KEYWORDS if kw.lower() in full_text)

    # Time features
    avg_hour   = float(np.mean(hours)) if hours else 12
    off_hours  = int(avg_hour < 7 or avg_hour > 22)

    # Component diversity
    n_comp     = len(components)

    return {
        "event_type_encoded":         round(avg_level, 4),
        "hour_of_day":                round(avg_hour, 2),
        "day_of_week":                0,
        "failed_logins_last_5min":    n_errors,
        "is_new_source_ip":           off_hours,
        "privilege_level":            max_level,
        "command_risk_score":         round(error_rate, 4),
        "is_first_time_user_host":    int(n_critical > 0),
        "time_since_last_event_sec":  n,
        "process_whitelisted":        int(n_errors == 0 and n_critical == 0),
        "destination_ip_internal":    1,
        "auth_method_encoded":        0,
        "dna_deviation_score":        round(min(100, n_critical * 25 + n_error_kw * 10), 2),
        "consecutive_failures":       n_errors + n_warnings,
        "session_duration_seconds":   n * 10,
    }


def parse():
    if not LOG_PATH.exists():
        print(f"❌ Log file not found: {LOG_PATH}")
        print(f"   Place HDFS_2k.log inside the log_model/ folder")
        return False

    print(f"Parsing: {LOG_PATH}")

    # ── Read and parse all lines ───────────────────────────────────────────
    parsed = []
    skipped = 0
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            result = parse_line(raw_line)
            if result:
                result["block_id"] = extract_block_id(result["content"])
                parsed.append(result)
            else:
                skipped += 1

    print(f"   Parsed: {len(parsed)} lines | Skipped: {skipped}")

    if not parsed:
        print("❌ No lines parsed — check log file format")
        return False

    df = pd.DataFrame(parsed)

    # ── Group by block_id ──────────────────────────────────────────────────
    has_block = df.dropna(subset=["block_id"])
    no_block  = df[df["block_id"].isna()]

    print(f"   Lines with block_id: {len(has_block)} | Without: {len(no_block)}")

    rows = []

    # Features per block
    for block_id, group in has_block.groupby("block_id"):
        features = build_features(group.to_dict("records"))
        # Heuristic label: block has errors/critical keywords = anomaly
        features["label"] = int(
            features["command_risk_score"] > 0.3 or
            features["privilege_level"] >= 2 or
            features["dna_deviation_score"] > 25
        )
        rows.append(features)

    # Features for lines without block_id (group by pid instead)
    if len(no_block) > 0:
        for pid, group in no_block.groupby("pid"):
            features = build_features(group.to_dict("records"))
            features["label"] = int(features["command_risk_score"] > 0.3)
            rows.append(features)

    features_df = pd.DataFrame(rows)
    n_anomaly   = features_df["label"].sum()

    print(f"   Feature vectors: {len(features_df)}")
    print(f"   Normal: {len(features_df) - n_anomaly} | Anomaly: {n_anomaly}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✅ Saved to: {OUTPUT_PATH}")
    return True


if __name__ == "__main__":
    success = parse()
    if not success:
        print("\nFalling back to synthetic data generation...")
        from generate_synthetic_logs import generate_logs
        generate_logs()