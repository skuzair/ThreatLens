"""
demo_dna.py
────────────
Standalone demo for the ThreatLens DNA Engine.

Shows THREE phases clearly:

PHASE 1 — LEARNING (10 events)
    Engine builds a behavioral baseline for device 192.168.1.157
    Normal traffic: ~2000-4000 bytes, daytime hours
    DNA scores stay LOW as it learns what "normal" looks like

PHASE 2 — STABLE (5 events)
    Baseline is now established
    Same normal traffic continues
    DNA scores remain LOW — device is behaving as expected

PHASE 3 — ATTACK (5 events)
    Suddenly: massive data exfiltration + unusual hours
    DNA scores SPIKE — device is way outside its normal profile
    This is the alert moment

Run from ThreatLens root:
    python demo_dna.py

Requirements:
    - Redis running (docker-compose up -d)
    - dna_engine folder in project root
"""

import sys
import os
import time
import random

# ── Path setup ─────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

try:
    from dna_engine.infer import DNAEngine
except ImportError as e:
    print(f"ERROR: Could not import DNAEngine: {e}")
    print("Make sure you are running from the ThreatLens root directory")
    print("and that Redis is running (docker-compose up -d)")
    sys.exit(1)


# ── Helpers ────────────────────────────────────────────────────────────────

def print_header(text):
    print("\n" + "=" * 65)
    print(f"  {text}")
    print("=" * 65)


def print_result(event_num, features, result, phase):
    dna        = result["dna"]
    score      = dna["overall_dna_deviation_score"]
    sigma      = dna["deviation_sigma"]
    anomalous  = dna["anomalous_metrics"]

    # Score indicator
    if score >= 70:
        indicator = "🔴 CRITICAL"
    elif score >= 40:
        indicator = "🟠 HIGH    "
    elif score >= 20:
        indicator = "🟡 MEDIUM  "
    else:
        indicator = "🟢 LOW     "

    print(f"\n  Event #{event_num:02d} | {indicator} | DNA Score: {score:6.2f} | Sigma: {sigma:5.2f}")
    print(f"           Bytes: {int(features['bytes_sent']):>9,} | "
          f"Hour: {int(features['hour_of_day']):02d}:00 | "
          f"Duration: {features['duration']:.1f}s")

    if anomalous:
        print(f"           Anomalous metrics detected:")
        for m in anomalous:
            print(f"             ⚠  {m['metric']:20s} "
                  f"current={m['current']:>12,.1f}  "
                  f"baseline={m['baseline_mean']:>12,.1f}  "
                  f"sigma={m['sigma']:.1f}x")


def run_demo():
    engine      = DNAEngine()
    entity_type = "device"
    entity_id   = "192.168.1.157"

    # Clear any existing profile for clean demo
    try:
        engine.store.client.delete(f"dna:{entity_type}:{entity_id}")
        print("✅ Cleared existing profile for clean demo")
    except Exception:
        pass

    event_num = 0

    # ── PHASE 1: Learning ──────────────────────────────────────────────────
    print_header("PHASE 1 — LEARNING BASELINE  (10 events)")
    print("  Device 192.168.1.157 sending normal corporate traffic.")
    print("  Engine is building behavioral profile...")
    print("  Expect: LOW scores — no baseline established yet\n")

    for i in range(10):
        event_num += 1
        features = {
            "bytes_sent":     random.randint(1500, 4500),    # normal: 1.5-4.5 KB
            "bytes_received": random.randint(800, 3000),
            "duration":       random.uniform(0.5, 5.0),
            "dest_port":      random.choice([80, 443, 8080, 22]),
            "hour_of_day":    random.randint(9, 17),          # business hours
        }

        result = engine.process_event(entity_type, entity_id, features)
        print_result(event_num, features, result, "learning")
        time.sleep(0.4)

    # ── PHASE 2: Stable ────────────────────────────────────────────────────
    print_header("PHASE 2 — STABLE BASELINE  (5 events)")
    print("  Same device, same normal behavior.")
    print("  Profile is now established.")
    print("  Expect: LOW scores — behavior matches profile\n")

    for i in range(5):
        event_num += 1
        features = {
            "bytes_sent":     random.randint(2000, 4000),
            "bytes_received": random.randint(1000, 2500),
            "duration":       random.uniform(1.0, 4.0),
            "dest_port":      random.choice([80, 443, 8080]),
            "hour_of_day":    random.randint(10, 16),
        }

        result = engine.process_event(entity_type, entity_id, features)
        print_result(event_num, features, result, "stable")
        time.sleep(0.4)

    # ── PHASE 3: Attack ────────────────────────────────────────────────────
    print_header("PHASE 3 — ATTACK DETECTED  (5 events)")
    print("  SAME device — but now exfiltrating data at 2AM!")
    print("  Massive byte spike + unusual hours = way outside profile.")
    print("  Expect: HIGH/CRITICAL scores — behavioral anomaly\n")

    for i in range(5):
        event_num += 1
        features = {
            "bytes_sent":     random.randint(50_000_000, 200_000_000),  # 50-200 MB exfil
            "bytes_received": random.randint(100, 500),                  # tiny response
            "duration":       random.uniform(30.0, 120.0),               # long connection
            "dest_port":      443,
            "hour_of_day":    random.randint(1, 4),                      # 1-4 AM
        }

        result = engine.process_event(entity_type, entity_id, features)
        print_result(event_num, features, result, "attack")
        time.sleep(0.4)

    # ── Summary ────────────────────────────────────────────────────────────
    print_header("DEMO COMPLETE")
    print("  What the DNA engine proved:")
    print()
    print("  Phase 1 (Learning):  Scores LOW — building profile from scratch")
    print("  Phase 2 (Stable):    Scores LOW — device behaving normally")
    print("  Phase 3 (Attack):    Scores SPIKE — massive deviation from baseline")
    print()
    print("  Key insight: No hardcoded thresholds.")
    print("  The engine learned what THIS device normally does,")
    print("  then flagged when it suddenly acted completely differently.")
    print()
    print("  This catches attacks that bypass signature-based detection")
    print("  because it asks 'is this normal FOR THIS device?' not")
    print("  'does this match a known attack pattern?'")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_demo()