import random

def simulate_behavior(input_data):
    return {
        "files_created": ["/tmp/.hidden", "C:/ransom_note.txt"],
        "files_encrypted": random.randint(200, 1000),
        "ransom_note_created": True,
        "registry_modified": ["HKCU\\Run\\persist_malware"],
        "shadow_copies_deleted": True,
        "processes_spawned_suspicious": ["cmd.exe", "vssadmin.exe"],
        "network_connections_attempted": [
            {"ip": "203.0.113.5", "port": 443, "domain": "evil-c2.ru"},
            {"ip": "198.51.100.3", "port": 8080}
        ]
    }
