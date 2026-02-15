"""
Attack Script Generator
=======================
Generates realistic but harmless attack simulation scripts that run
inside the Docker container. Each script mimics real malware behaviour
(file ops, network probes, registry reads) using only stdlib — nothing
actually harmful leaves the container.
"""

RANSOMWARE_SCRIPT = '''
import os, time, hashlib, random, socket, json
from pathlib import Path

ROOT = Path("/sandbox/victim_files")
ROOT.mkdir(parents=True, exist_ok=True)

LOG = []

def log(msg):
    print(msg, flush=True)
    LOG.append(msg)

log("[*] Ransomware payload initialising...")
log(f"[*] Host: {socket.gethostname()}")
log(f"[*] PID:  {os.getpid()}")
time.sleep(0.3)

# --- Phase 1: Reconnaissance ---
log("\\n[PHASE 1] File system enumeration")
extensions = [".xlsx", ".docx", ".pdf", ".csv", ".txt", ".db", ".sql", ".bak"]
victim_files = []
for i, ext in enumerate(extensions * 20):
    fname = ROOT / f"document_{i:04d}{ext}"
    content = f"CONFIDENTIAL DATA {i} " * 50
    fname.write_text(content)
    victim_files.append(fname)
log(f"[+] Enumerated {len(victim_files)} files for encryption")
time.sleep(0.2)

# --- Phase 2: C2 Beacon ---
log("\\n[PHASE 2] C2 communication")
c2_hosts = ["185.220.101.47", "91.108.4.200", "secure-payments.xyz"]
for host in c2_hosts:
    log(f"[*] Attempting beacon to {host}:443 ...")
    time.sleep(0.15)
    log(f"[+] Beacon sent (simulated) — key exchange complete")

xor_key = 0xDE
log(f"[+] Encryption key received: {hashlib.sha256(bytes([xor_key]*32)).hexdigest()[:16]}...")
time.sleep(0.2)

# --- Phase 3: Disable Backups ---
log("\\n[PHASE 3] Defence evasion")
shadow_cmds = [
    "vssadmin delete shadows /all /quiet",
    "wbadmin delete catalog -quiet",
    "bcdedit /set {default} recoveryenabled No",
]
for cmd in shadow_cmds:
    log(f"[*] Exec: {cmd}")
    time.sleep(0.1)
log("[+] Shadow copies destroyed — recovery blocked")

# --- Phase 4: Encryption ---
log("\\n[PHASE 4] File encryption")
encrypted = 0
for f in victim_files:
    data = f.read_bytes()
    enc  = bytes(b ^ xor_key for b in data)
    enc_path = f.with_suffix(f.suffix + ".locked")
    enc_path.write_bytes(enc)
    f.unlink()
    encrypted += 1
    if encrypted % 30 == 0:
        log(f"[+] Encrypted {encrypted}/{len(victim_files)} files...")
    time.sleep(0.01)
log(f"[+] Encryption complete — {encrypted} files locked")

# --- Phase 5: Ransom Note ---
log("\\n[PHASE 5] Dropping ransom note")
note = (ROOT / "README_RESTORE.txt")
note.write_text(f"""YOUR FILES HAVE BEEN ENCRYPTED
Files locked: {encrypted}
Key ID: {hashlib.sha256(os.urandom(16)).hexdigest()}
Payment: 4.5 BTC within 72h
""")
log(f"[+] Ransom note written to {note}")

# --- Summary ---
result = {
    "phase": "complete",
    "files_encrypted": encrypted,
    "ransom_note_created": True,
    "shadow_copies_deleted": True,
    "c2_callbacks": len(c2_hosts),
    "registry_modified": ["HKCU\\\\Run\\\\persist"],
    "processes_spawned_suspicious": ["cmd.exe", "vssadmin.exe"],
    "network_connections_attempted": [
        {"ip": "185.220.101.47", "port": 443, "domain": "secure-payments.xyz"},
        {"ip": "91.108.4.200",   "port": 8080},
    ],
}
print("\\nSANDBOX_RESULT_JSON:" + json.dumps(result), flush=True)
'''

EXFIL_SCRIPT = '''
import os, time, hashlib, socket, json, random
from pathlib import Path

ROOT = Path("/sandbox/exfil_data")
ROOT.mkdir(parents=True, exist_ok=True)

LOG = []
def log(msg):
    print(msg, flush=True)

log("[*] Data exfiltration payload initialising...")
log(f"[*] Host: {socket.gethostname()}")
time.sleep(0.2)

# --- Phase 1: Credential Harvest ---
log("\\n[PHASE 1] Credential harvesting")
cred_targets = [
    "/etc/passwd", "/etc/shadow", "~/.ssh/id_rsa",
    "C:/Users/*/AppData/Roaming/credentials",
    "HKLM/SAM", "LSASS memory dump"
]
harvested = []
for t in cred_targets:
    log(f"[*] Probing: {t}")
    time.sleep(0.1)
    harvested.append({"target": t, "status": "accessed"})
log(f"[+] Harvested {len(harvested)} credential sources")

# --- Phase 2: Data Collection ---
log("\\n[PHASE 2] Sensitive data collection")
records = []
categories = ["PII", "Financial", "IP/Trade Secret", "Auth Tokens", "API Keys"]
for i in range(500):
    record = {
        "id": i,
        "category": random.choice(categories),
        "data": hashlib.md5(os.urandom(8)).hexdigest(),
    }
    records.append(record)
    if i % 100 == 0:
        log(f"[*] Collected {i+1} records...")
    time.sleep(0.005)

# Write collection archive
archive = ROOT / "exfil_package.json"
import json as _json
archive.write_text(_json.dumps(records, indent=2))
size_kb = archive.stat().st_size / 1024
log(f"[+] Archive ready: {size_kb:.1f} KB ({len(records)} records)")

# --- Phase 3: DNS Tunnelling ---
log("\\n[PHASE 3] Exfiltration via DNS tunnelling")
c2 = "update.microsofft-cdn.com"
chunks = [records[i:i+50] for i in range(0, len(records), 50)]
for idx, chunk in enumerate(chunks):
    encoded = hashlib.sha256(str(chunk).encode()).hexdigest()[:16]
    log(f"[*] DNS query: {encoded}.{c2} (chunk {idx+1}/{len(chunks)})")
    time.sleep(0.08)
log(f"[+] Exfiltration complete — {size_kb:.1f} KB sent via DNS")

# --- Phase 4: Cover Tracks ---
log("\\n[PHASE 4] Covering tracks")
logs_to_clear = ["Security.evtx", "System.evtx", "Application.evtx", "PowerShell.evtx"]
for l in logs_to_clear:
    log(f"[*] Clearing: {l}")
    time.sleep(0.05)
log("[+] Event logs wiped")

result = {
    "phase": "complete",
    "files_encrypted": 0,
    "ransom_note_created": False,
    "shadow_copies_deleted": False,
    "records_exfiltrated": len(records),
    "exfil_size_kb": round(size_kb, 2),
    "c2_callbacks": len(chunks),
    "registry_modified": [],
    "processes_spawned_suspicious": ["powershell.exe", "cmd.exe"],
    "network_connections_attempted": [
        {"ip": "185.220.101.47", "port": 443, "domain": c2},
        {"ip": "8.8.8.8",        "port": 53,  "domain": "dns-tunnel"},
    ],
}
print("\\nSANDBOX_RESULT_JSON:" + json.dumps(result), flush=True)
'''

SCRIPTS = {
    "ransomware":       RANSOMWARE_SCRIPT,
    "data_exfiltration": EXFIL_SCRIPT,
}

def get_script(attack_type: str) -> str:
    return SCRIPTS.get(attack_type, EXFIL_SCRIPT)