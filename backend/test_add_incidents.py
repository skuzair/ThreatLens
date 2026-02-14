"""
Test script to add sample incidents via the API
"""
import asyncio
import httpx
from datetime import datetime, timedelta

# API endpoint
API_BASE_URL = "http://localhost:8000/api/incidents/"


async def create_sample_incidents():
    """Create two sample incidents for testing"""
    
    # Sample Incident 1: Credential Theft Attack
    incident1 = {
        "incident_id": "INC-2026-001",
        "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "risk_score": 85,
        "severity": "HIGH",
        "rule_name": "Suspicious Login Pattern with Data Exfiltration",
        "sources_involved": ["logs", "network", "camera"],
        "intent_primary": "credential_theft",
        "intent_confidence": 0.89,
        "zone": "DMZ-A",
        "correlated_events": [
            {
                "event_id": "EVT-001",
                "source_type": "logs",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "score": 65,
                "description": "Multiple failed login attempts from unusual IP",
                "metadata": {
                    "source_ip": "192.168.10.45",
                    "username": "admin",
                    "attempts": 15,
                    "service": "SSH"
                }
            },
            {
                "event_id": "EVT-002",
                "source_type": "logs",
                "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=-5)).isoformat(),
                "score": 75,
                "description": "Successful login after brute force",
                "metadata": {
                    "source_ip": "192.168.10.45",
                    "username": "admin",
                    "service": "SSH",
                    "session_id": "sess_9876"
                }
            },
            {
                "event_id": "EVT-003",
                "source_type": "network",
                "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=-10)).isoformat(),
                "score": 80,
                "description": "Large data transfer to external IP",
                "metadata": {
                    "source_ip": "192.168.10.45",
                    "dest_ip": "185.220.102.8",
                    "bytes_transferred": 524288000,
                    "protocol": "HTTPS"
                }
            },
            {
                "event_id": "EVT-004",
                "source_type": "camera",
                "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=-20)).isoformat(),
                "score": 60,
                "description": "Unauthorized person detected in server room",
                "metadata": {
                    "camera_id": "CAM-SR-02",
                    "location": "Server Room A",
                    "confidence": 0.82,
                    "person_id": "unknown_001"
                }
            }
        ],
        "mitre_ttps": ["T1078", "T1110", "T1041", "T1071"],
        "current_attack_stage": "Exfiltration",
        "predicted_next_move": {
            "stage": "Cover Tracks",
            "confidence": 0.76,
            "actions": ["Log deletion", "Connection termination"]
        },
        "nlg_explanation": {
            "summary": "Detected coordinated attack involving physical access, credential brute force, and data exfiltration",
            "details": "An unauthorized person entered the server room, followed by multiple failed SSH login attempts and a successful compromise. Large volume of data was then transferred to an external IP address known for malicious activity.",
            "recommendations": [
                "Immediately revoke admin credentials and force password reset",
                "Block external IP 185.220.102.8 at firewall",
                "Review physical access logs and security camera footage",
                "Investigate data exfiltrated and assess impact"
            ]
        },
        "neo4j_node_ids": ["node_evt001", "node_evt002", "node_evt003", "node_evt004"]
    }
    
    # Sample Incident 2: Ransomware Attack
    incident2 = {
        "incident_id": "INC-2026-002",
        "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "risk_score": 95,
        "severity": "CRITICAL",
        "rule_name": "Ransomware Activity Detected",
        "sources_involved": ["file", "network", "logs"],
        "intent_primary": "ransomware",
        "intent_confidence": 0.94,
        "zone": "Production Network",
        "correlated_events": [
            {
                "event_id": "EVT-101",
                "source_type": "file",
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "score": 90,
                "description": "Suspicious executable detected in email attachment",
                "metadata": {
                    "filename": "invoice_2026.exe",
                    "file_hash": "d8f9a3b2c1e4567890abcdef12345678",
                    "sender": "accounting@fake-domain.com",
                    "recipient": "finance@company.local"
                }
            },
            {
                "event_id": "EVT-102",
                "source_type": "file",
                "timestamp": (datetime.utcnow() - timedelta(minutes=55)).isoformat(),
                "score": 95,
                "description": "Mass file encryption activity detected",
                "metadata": {
                    "files_encrypted": 1247,
                    "file_types": [".docx", ".xlsx", ".pdf", ".jpg"],
                    "new_extension": ".locked",
                    "affected_paths": ["\\\\server\\shared", "C:\\Users\\Documents"]
                }
            },
            {
                "event_id": "EVT-103",
                "source_type": "network",
                "timestamp": (datetime.utcnow() - timedelta(minutes=50)).isoformat(),
                "score": 85,
                "description": "C2 beacon communication detected",
                "metadata": {
                    "dest_ip": "45.142.212.61",
                    "dest_port": 443,
                    "protocol": "HTTPS",
                    "beacon_interval": 60,
                    "data_sent_bytes": 2048
                }
            },
            {
                "event_id": "EVT-104",
                "source_type": "logs",
                "timestamp": (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
                "score": 88,
                "description": "Shadow copy deletion via vssadmin",
                "metadata": {
                    "command": "vssadmin.exe delete shadows /all /quiet",
                    "user": "SYSTEM",
                    "parent_process": "invoice_2026.exe"
                }
            }
        ],
        "mitre_ttps": ["T1566", "T1486", "T1490", "T1071", "T1059"],
        "current_attack_stage": "Impact",
        "predicted_next_move": {
            "stage": "Ransom Note Display",
            "confidence": 0.91,
            "actions": ["Display ransom note", "Payment instructions"]
        },
        "nlg_explanation": {
            "summary": "Active ransomware attack in progress with file encryption and backup deletion",
            "details": "A malicious executable was delivered via phishing email and executed on finance workstation. The malware is actively encrypting files across network shares and has deleted volume shadow copies to prevent recovery. Command and control communication has been established with known ransomware infrastructure.",
            "recommendations": [
                "IMMEDIATE: Isolate affected systems from network",
                "IMMEDIATE: Block C2 IP 45.142.212.61 at perimeter firewall",
                "Disable user account that opened malicious attachment",
                "Do not pay ransom - initiate backup recovery procedures",
                "Preserve forensic image of affected systems",
                "Contact incident response team and law enforcement"
            ]
        },
        "neo4j_node_ids": ["node_evt101", "node_evt102", "node_evt103", "node_evt104"]
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("Creating sample incidents...\n")
        
        # Create Incident 1
        try:
            response1 = await client.post(API_BASE_URL, json=incident1, timeout=10.0)
            if response1.status_code == 201:
                print(f"✓ Successfully created Incident 1: {incident1['incident_id']}")
                print(f"  Severity: {incident1['severity']}, Risk Score: {incident1['risk_score']}")
                print(f"  Intent: {incident1['intent_primary']}\n")
            else:
                print(f"✗ Failed to create Incident 1: {response1.status_code}")
                print(f"  Response: {response1.text}\n")
        except Exception as e:
            print(f"✗ Error creating Incident 1: {str(e)}\n")
        
        # Create Incident 2
        try:
            response2 = await client.post(API_BASE_URL, json=incident2, timeout=10.0)
            if response2.status_code == 201:
                print(f"✓ Successfully created Incident 2: {incident2['incident_id']}")
                print(f"  Severity: {incident2['severity']}, Risk Score: {incident2['risk_score']}")
                print(f"  Intent: {incident2['intent_primary']}\n")
            else:
                print(f"✗ Failed to create Incident 2: {response2.status_code}")
                print(f"  Response: {response2.text}\n")
        except Exception as e:
            print(f"✗ Error creating Incident 2: {str(e)}\n")
        
        # Verify by listing incidents
        print("Verifying incidents...")
        try:
            list_response = await client.get(API_BASE_URL, params={"limit": 10}, timeout=10.0)
            if list_response.status_code == 200:
                data = list_response.json()
                print(f"✓ Total incidents in database: {data['total']}")
                print(f"  Retrieved {len(data['incidents'])} incidents\n")
                
                for inc in data['incidents']:
                    print(f"  - {inc['incident_id']}: {inc['severity']} | {inc['rule_name']}")
            else:
                print(f"✗ Failed to list incidents: {list_response.status_code}")
        except Exception as e:
            print(f"✗ Error listing incidents: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("ThreatLens - Sample Incidents Test")
    print("=" * 60)
    print(f"Target API: {API_BASE_URL}\n")
    
    asyncio.run(create_sample_incidents())
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
