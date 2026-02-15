"""
Test Evidence Capture Locally (Without Kafka)

This script tests the evidence capture system in standalone mode.
Run from ThreatLens root directory: python demo_evidence.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Disable Kafka for local testing
os.environ["ENABLE_KAFKA"] = "false"

# Add evidence_capture to path
sys.path.insert(0, str(Path(__file__).parent / "evidence_capture"))

from orchestrator import process_incident


# Sample incident (similar to what correlation engine produces)
test_incidents = [
    {
        "incident_id": "INC-TEST-EXFIL",
        "risk_score": 89.5,
        "severity": "HIGH",
        "intent": {
            "primary": "data_exfiltration",
            "primary_confidence": 0.87
        },
        "correlated_events": [
            {
                "event_id": "cam-001",
                "source": "camera",
                "score": 85,
                "zone": "server_room",
                "timestamp": "2026-02-15T14:23:00Z"
            },
            {
                "event_id": "log-001",
                "source": "logs",
                "score": 72,
                "zone": "server_room",
                "timestamp": "2026-02-15T14:24:00Z"
            },
            {
                "event_id": "net-001",
                "source": "network",
                "score": 88,
                "zone": "server_room",
                "timestamp": "2026-02-15T14:25:00Z",
                "source_ip": "192.168.1.100",
                "dest_ip": "8.8.8.8"
            }
        ],
        "timestamp_range": {
            "start": "2026-02-15T14:23:00Z",
            "end": "2026-02-15T14:25:30Z"
        },
        "sources_involved": ["camera", "logs", "network"],
        "zone": "server_room"
    },
    {
        "incident_id": "INC-TEST-RANSOMWARE",
        "risk_score": 95.0,
        "severity": "CRITICAL",
        "intent": {
            "primary": "ransomware",
            "primary_confidence": 0.95
        },
        "correlated_events": [
            {
                "event_id": "file-001",
                "source": "file",
                "score": 95,
                "zone": "internal",
                "timestamp": "2026-02-15T14:30:00Z",
                "ransomware_pattern": True
            },
            {
                "event_id": "net-002",
                "source": "network",
                "score": 78,
                "zone": "internal",
                "timestamp": "2026-02-15T14:31:00Z"
            }
        ],
        "timestamp_range": {
            "start": "2026-02-15T14:30:00Z",
            "end": "2026-02-15T14:31:30Z"
        },
        "sources_involved": ["file", "network"],
        "zone": "internal"
    }
]


async def main():
    print("\n" + "="*80)
    print("  EVIDENCE CAPTURE - STANDALONE DEMO")
    print("="*80)
    print("\n📝 Testing evidence capture for multiple incident types...")
    print("🔌 Kafka: DISABLED (local mode)\n")
    
    results = []
    
    for incident in test_incidents:
        print("\n" + "-"*80)
        print(f"Processing: {incident['incident_id']}")
        print(f"Type: {incident['intent']['primary']}")
        print(f"Severity: {incident['severity']}")
        print("-"*80 + "\n")
        
        try:
            manifest = await process_incident(incident)
            results.append((incident['incident_id'], True, manifest))
            
            print(f"\n✅ Success!")
            print(f"   Size: {manifest['total_size_mb']} MB")
            print(f"   Location: {manifest['folder_path']}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            results.append((incident['incident_id'], False, str(e)))
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print("  📊 DEMO SUMMARY")
    print("="*80 + "\n")
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    print(f"Processed: {success_count}/{total_count} incidents")
    print()
    
    for incident_id, success, data in results:
        status = "✅" if success else "❌"
        print(f"{status} {incident_id}")
        if success and isinstance(data, dict):
            print(f"   → {data['folder_path']}")
    
    print("\n💡 Evidence folders created in:")
    evidence_root = Path(__file__).parent / "evidence"
    print(f"   {evidence_root.absolute()}")
    
    print("\n🎯 Next steps:")
    print("   1. Check evidence folders for captured data")
    print("   2. Review manifest.json files")
    print("   3. Enable Kafka to publish manifests: set ENABLE_KAFKA=true")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())