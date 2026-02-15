"""
demo_file.py
─────────────
Standalone demo for ThreatLens File Anomaly Detection.

Shows THREE phases:

PHASE 1 — NORMAL office file activity  → LOW scores
PHASE 2 — SUSPICIOUS activity          → MEDIUM/HIGH scores
PHASE 3 — RANSOMWARE pattern           → CRITICAL scores

Run from ThreatLens root:
    python demo_file.py
"""

import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

try:
    from file_model.infer import FileAnomalyPredictor
except ImportError as e:
    print(f"ERROR: {e}")
    print("Make sure file_model/ is in your ThreatLens root directory")
    sys.exit(1)


def print_header(text):
    print("\n" + "=" * 65)
    print(f"  {text}")
    print("=" * 65)


def print_result(event_num, sample, result):
    score      = result["anomaly_score"]
    is_anomaly = result["is_anomaly"]
    rules      = []

    # Quick rule check for display
    mpm, upw, ecr, fscr, sdar, hour = sample
    if mpm > 50:              rules.append("mass_modification")
    if ecr > 0.5:             rules.append("bulk_extension_change")
    if sdar > 0.4:            rules.append("sensitive_dir_access")
    if mpm > 100 and ecr > 0.6: rules.append("🚨 RANSOMWARE_PATTERN")

    if score >= 80:   indicator = "🔴 CRITICAL"
    elif score >= 60: indicator = "🟠 HIGH    "
    elif score >= 40: indicator = "🟡 MEDIUM  "
    else:             indicator = "🟢 LOW     "

    print(f"\n  Event #{event_num:02d} | {indicator} | Score: {score:6.2f}/100")
    print(f"           Mods/min: {int(mpm):>4} | "
          f"ExtChange: {ecr:.2f} | "
          f"SensitiveDir: {sdar:.2f} | "
          f"Hour: {int(hour):02d}:00")
    if rules:
        print(f"           Rules triggered: {', '.join(rules)}")


def run_demo():
    print_header("ThreatLens AI — File Anomaly Detection Demo")
    print("  Loading model...")

    try:
        predictor = FileAnomalyPredictor()
        print("  ✅ Model loaded\n")
    except Exception as e:
        print(f"  ❌ {e}")
        return

    event_num = 0

    # ── Phase 1: Normal ───────────────────────────────────────────────────
    print_header("PHASE 1 — NORMAL FILE ACTIVITY")
    print("  Regular office work: documents, spreadsheets, emails")
    print("  Expect: LOW scores\n")

    normal_samples = [
        [1, 1, 0.01, 1.02, 0.03, 10],   # morning, 1 mod/min, no ext change
        [3, 2, 0.02, 0.98, 0.05, 14],   # afternoon, 3 mods/min
        [2, 1, 0.00, 1.00, 0.02, 16],   # late afternoon, normal
        [4, 2, 0.01, 1.01, 0.04, 11],   # mid morning
        [1, 1, 0.00, 0.99, 0.01, 9],    # early morning
    ]

    for sample in normal_samples:
        event_num += 1
        result = predictor.predict(sample)
        print_result(event_num, sample, result)
        time.sleep(0.3)

    # ── Phase 2: Suspicious ───────────────────────────────────────────────
    print_header("PHASE 2 — SUSPICIOUS ACTIVITY")
    print("  Unusual modification rates, off-hours access")
    print("  Expect: MEDIUM/HIGH scores\n")

    suspicious_samples = [
        [15, 2, 0.15, 0.85, 0.20, 6],   # early morning, higher rate
        [25, 2, 0.25, 0.75, 0.30, 4],   # 4am, extension changes
        [30, 3, 0.20, 0.80, 0.35, 3],   # 3am, sensitive dirs
        [20, 2, 0.18, 0.82, 0.25, 5],   # 5am, unusual activity
    ]

    for sample in suspicious_samples:
        event_num += 1
        result = predictor.predict(sample)
        print_result(event_num, sample, result)
        time.sleep(0.3)

    # ── Phase 3: Ransomware ───────────────────────────────────────────────
    print_header("PHASE 3 — RANSOMWARE PATTERN DETECTED")
    print("  Mass file encryption: 100+ mods/min, bulk extension changes")
    print("  Expect: CRITICAL scores\n")

    ransomware_samples = [
        [140, 1, 0.80, 0.40, 0.70, 2],  # 2am, 140 mods/min, 80% ext change
        [165, 1, 0.90, 0.30, 0.85, 1],  # 1am, 165 mods/min, 90% ext change
        [182, 1, 0.95, 0.25, 0.90, 2],  # full ransomware
        [200, 1, 1.00, 0.20, 0.95, 3],  # peak ransomware
    ]

    for sample in ransomware_samples:
        event_num += 1
        result = predictor.predict(sample)
        print_result(event_num, sample, result)
        time.sleep(0.3)

    # ── Summary ───────────────────────────────────────────────────────────
    print_header("DEMO COMPLETE")
    print("  What the File Detection model proved:")
    print()
    print("  Phase 1 (Normal):     LOW scores    — normal office activity")
    print("  Phase 2 (Suspicious): MEDIUM/HIGH   — unusual hours + rates")
    print("  Phase 3 (Ransomware): CRITICAL       — mass encryption pattern")
    print()
    print("  Key features that trigger ransomware detection:")
    print("    • modifications_per_minute > 100")
    print("    • extension_change_rate    > 0.6  (.docx → .encrypted)")
    print("    • sensitive_dir_access     > 0.7")
    print("    • hour_of_day              1-4 AM (off hours)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_demo()