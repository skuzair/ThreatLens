"""
Correlation Engine Test - Standalone Version
Run this from ThreatLens root directory: python test_correlation.py
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Ensure correlation_engine is in path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_section(title):
    print("\n" + "-"*80)
    print(f"  {title}")
    print("-"*80)

# ============================================================
# Import with error handling
# ============================================================
try:
    from correlation_engine.infer import CorrelationEngine
    from correlation_engine.correlation_window import CorrelationWindowManager
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\n🔧 Troubleshooting steps:")
    print("1. Make sure you're in the ThreatLens root directory")
    print("2. Verify correlation_engine/ folder exists")
    print("3. Check that these files are present:")
    print("   - correlation_engine/risk_calculator.py")
    print("   - correlation_engine/intent_predictor.py")
    print("   - correlation_engine/rules_config.py")
    print("   - correlation_engine/rule_engine.py")
    print("   - correlation_engine/markov_predictor.py")
    print("\n4. Try copying files again:")
    print("   cp correlation_engine_updated/* correlation_engine/")
    sys.exit(1)

# ============================================================
# Test Scenarios
# ============================================================

def create_test_scenarios():
    """Create test scenarios"""
    
    base_time = datetime.utcnow()
    
    return [
        # Scenario 1: Data Exfiltration
        {
            "name": "Insider Data Exfiltration",
            "description": "Employee exfiltrating data",
            "events": [
                {
                    "event_id": "cam-001",
                    "source": "camera",
                    "score": 85,
                    "zone": "server_room",
                    "timestamp": (base_time - timedelta(minutes=2)).isoformat() + "Z",
                },
                {
                    "event_id": "log-001",
                    "source": "logs",
                    "score": 72,
                    "zone": "server_room",
                    "timestamp": (base_time - timedelta(minutes=1)).isoformat() + "Z",
                },
                {
                    "event_id": "net-001",
                    "source": "network",
                    "score": 88,
                    "zone": "server_room",
                    "timestamp": base_time.isoformat() + "Z",
                    "large_transfer_flag": True,
                }
            ],
        },
        
        # Scenario 2: Ransomware
        {
            "name": "Ransomware Deployment",
            "description": "Mass file encryption",
            "events": [
                {
                    "event_id": "file-001",
                    "source": "file",
                    "score": 95,
                    "zone": "internal",
                    "timestamp": (base_time - timedelta(minutes=1)).isoformat() + "Z",
                    "ransomware_pattern": True,
                },
                {
                    "event_id": "net-002",
                    "source": "network",
                    "score": 78,
                    "zone": "internal",
                    "timestamp": base_time.isoformat() + "Z",
                }
            ],
        },
        
        # Scenario 3: Credential Attack
        {
            "name": "Brute Force Attack",
            "description": "Multiple failed logins",
            "events": [
                {
                    "event_id": "log-003",
                    "source": "logs",
                    "score": 82,
                    "zone": "dmz",
                    "timestamp": base_time.isoformat() + "Z",
                }
            ],
        },
    ]

# ============================================================
# Main Test
# ============================================================

def run_tests():
    print_header("🔍 THREATLENS CORRELATION ENGINE TEST")
    
    print("📦 Initializing...")
    try:
        engine = CorrelationEngine()
        window_manager = CorrelationWindowManager(
            window_size_minutes=15,
            anomaly_threshold=40
        )
        print("✅ Engine initialized\n")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    scenarios = create_test_scenarios()
    print(f"🎯 Running {len(scenarios)} test scenarios...\n")
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print_section(f"TEST {i}: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Events: {len(scenario['events'])}\n")
        
        # Add events
        for event in scenario['events']:
            window_manager.add_event(event)
            print(f"  + [{event['source'].upper():8}] Score: {event['score']}%")
        
        # Get windows
        windows = window_manager.get_active_windows()
        
        if not windows:
            print("\n  ⚠️  No windows matched")
            results.append({"name": scenario['name'], "status": "NO_WINDOW"})
            window_manager.clear_zone("server_room")
            window_manager.clear_zone("internal")
            window_manager.clear_zone("dmz")
            continue
        
        # Process
        try:
            result = engine.process(windows[0])
            
            if not result:
                print("\n  ⚠️  No rule matched")
                results.append({"name": scenario['name'], "status": "NO_RULE"})
            else:
                print(f"\n  ✅ INCIDENT DETECTED")
                print(f"     ID:       {result['incident_id']}")
                print(f"     Risk:     {result['risk_score']}/100")
                print(f"     Severity: {result['severity']}")
                print(f"     Intent:   {result['intent']['primary_intent']} ({result['intent']['primary_confidence']*100:.1f}%)")
                print(f"     Stage:    {result['attack_progression']['current_stage']}")
                print(f"     Next:     {result['attack_progression']['predicted_next_stage']}")
                
                results.append({
                    "name": scenario['name'],
                    "status": "DETECTED",
                    "risk": result['risk_score'],
                    "severity": result['severity']
                })
        except Exception as e:
            print(f"\n  ❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
            results.append({"name": scenario['name'], "status": "ERROR"})
        
        # Clear zone
        if windows:
            window_manager.clear_zone(windows[0]['zone'])
        print()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    detected = sum(1 for r in results if r['status'] == 'DETECTED')
    total = len(results)
    
    for i, r in enumerate(results, 1):
        status_emoji = "✅" if r['status'] == "DETECTED" else "⚠️"
        print(f"{status_emoji} [{i}] {r['name']}: {r['status']}")
        if 'risk' in r:
            print(f"      Risk: {r['risk']}/100 | Severity: {r['severity']}")
    
    print(f"\n📈 Detection Rate: {detected}/{total} ({detected/total*100:.0f}%)")
    
    if detected == total:
        print("🎉 ALL TESTS PASSED!\n")
    elif detected > 0:
        print("✓ Partial success - some detections working\n")
    else:
        print("⚠️  No detections - check configuration\n")

if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n⏸️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()