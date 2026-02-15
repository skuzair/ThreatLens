"""
Sandbox Service Demo
====================
Runs the full sandbox pipeline for two attack types without Kafka.

Usage (from ThreatLens root):
    python demo_sandbox.py

Requirements:
    pip install pillow
    Docker running (falls back to subprocess if not)
"""

import os
import sys
import time
from pathlib import Path

os.environ["ENABLE_KAFKA"] = "false"

# Always resolve sandbox_service relative to this file
SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox_service"
sys.path.insert(0, str(SANDBOX_DIR))

from sandbox_orchestrator import execute_sandbox

TEST_CASES = [
    {
        "incident_id": "INC-DEMO-RANSOMWARE",
        "file_hash":   "sha256:4a8b2c1d9e3f0a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b",
        "attack_type": "ransomware",
    },
    {
        "incident_id": "INC-DEMO-EXFIL",
        "file_hash":   "sha256:1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
        "attack_type": "data_exfiltration",
    },
]


def main():
    print("\n" + "═" * 80)
    print("  THREATLENS SANDBOX SERVICE — DEMO")
    print("═" * 80)

    results = []

    for case in TEST_CASES:
        inc_id = case["incident_id"]
        atype  = case["attack_type"]

        print(f"\n{'─'*80}")
        print(f"  ▶ {inc_id}  [{atype.upper().replace('_',' ')}]")
        print(f"{'─'*80}")

        t0 = time.time()
        try:
            result = execute_sandbox(case)
            elapsed = time.time() - t0
            results.append((inc_id, True, result, elapsed))
        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append((inc_id, False, str(e), time.time() - t0))

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'═'*80}")
    print("  📊  DEMO SUMMARY")
    print(f"{'═'*80}\n")

    for inc_id, ok, data, elapsed in results:
        if ok:
            r = data
            print(f"  ✅  {inc_id}")
            print(f"      Verdict:     {r['verdict']}  ({r['confidence_score']}%)")
            print(f"      Docker:      {r['docker_used']}")
            print(f"      Duration:    {r['duration_sec']}s container + {elapsed:.1f}s total")
            print(f"      Frames:      {r['screenshot_count']}")
            print(f"      Indicators:  {', '.join(r['indicators'])}")
            print(f"      IOCs:        {len(r['extracted_iocs'].get('ips', []))} IPs, "
                  f"{len(r['extracted_iocs'].get('domains', []))} domains")
            frame_dir = Path(r['screenshot_sequence'][0]).parent if r['screenshot_sequence'] else "—"
            print(f"      Frames at:   {frame_dir}")
        else:
            print(f"  ❌  {inc_id}: {data}")
        print()

    print("═" * 80 + "\n")


if __name__ == "__main__":
    main()