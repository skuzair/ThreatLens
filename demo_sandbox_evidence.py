"""
ThreatLens — Sandbox + Evidence Capture (Combined Demo)
=======================================================
Full integrated pipeline:

  1. Sandbox detonates malware in an isolated Docker container
  2. Evidence is captured *from* the sandbox in real time:
       - camera/   : PIL-rendered frames of the executing malware
       - network/  : PCAP built from the container's C2 connection attempts
       - logs/     : Structured JSON from the container's stdout + IOCs
       - files/    : Encrypted file artifacts produced by the malware
  3. Threat timeline reconstructed from sandbox phases
  4. SHA-256 chain manifest for blockchain anchoring

Run from ThreatLens root:
    python demo_sandbox_evidence.py

Requirements:
    pip install pillow
    Docker running (falls back to subprocess if Docker unavailable)
"""

import asyncio
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

# ── PIL availability ──────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[!] Pillow not found — camera frames will be skipped.")
    print("    Install with: pip install pillow\n")

# ── Config ────────────────────────────────────────────────────────────────
os.environ["ENABLE_KAFKA"] = "false"

ROOT          = Path(__file__).resolve().parent
EVIDENCE_ROOT = ROOT / "evidence"
EVIDENCE_ROOT.mkdir(exist_ok=True)

DOCKER_IMAGE  = "python:3.11-slim"
NUM_FRAMES    = 30
DOCKER_MEM    = "256m"
DOCKER_CPUS   = "0.5"

# ═══════════════════════════════════════════════════════════════════════════
# ATTACK SCRIPTS (injected into Docker)
# ═══════════════════════════════════════════════════════════════════════════

ATTACK_SCRIPTS = {

"ransomware": '''
import os, time, hashlib, random, socket, json
from pathlib import Path

ROOT = Path("/sandbox/victim_files")
ROOT.mkdir(parents=True, exist_ok=True)

def log(msg): print(msg, flush=True)

log("[*] Ransomware payload initialising...")
log(f"[*] Host: {socket.gethostname()}  PID: {os.getpid()}")
time.sleep(0.2)

log("\\n[PHASE 1] File system enumeration")
extensions = [".xlsx",".docx",".pdf",".csv",".txt",".db",".sql",".bak"]
victim_files = []
for i, ext in enumerate(extensions * 20):
    f = ROOT / f"document_{i:04d}{ext}"
    f.write_text(f"CONFIDENTIAL DATA {i} " * 40)
    victim_files.append(f)
log(f"[+] Enumerated {len(victim_files)} files for encryption")
time.sleep(0.15)

log("\\n[PHASE 2] C2 communication")
c2_hosts = ["185.220.101.47","91.108.4.200","secure-payments.xyz"]
for h in c2_hosts:
    log(f"[*] Beacon → {h}:443 ...")
    time.sleep(0.1)
    log(f"[+] Beacon sent — key exchange complete")
xor_key = 0xDE
log(f"[+] Key received: {hashlib.sha256(bytes([xor_key]*32)).hexdigest()[:16]}...")

log("\\n[PHASE 3] Defence evasion")
for cmd in ["vssadmin delete shadows /all /quiet",
            "wbadmin delete catalog -quiet",
            "bcdedit /set {default} recoveryenabled No"]:
    log(f"[*] Exec: {cmd}"); time.sleep(0.08)
log("[+] Shadow copies destroyed")

log("\\n[PHASE 4] File encryption")
encrypted = 0
for f in victim_files:
    enc = bytes(b ^ xor_key for b in f.read_bytes())
    f.with_suffix(f.suffix+".locked").write_bytes(enc)
    f.unlink(); encrypted += 1
    if encrypted % 40 == 0: log(f"[+] Encrypted {encrypted}/{len(victim_files)}...")
    time.sleep(0.008)
log(f"[+] Encryption complete — {encrypted} files locked")

log("\\n[PHASE 5] Ransom note")
note = ROOT / "README_RESTORE.txt"
note.write_text(f"FILES ENCRYPTED\\nCount: {encrypted}\\nBTC: 4.5\\n72h deadline")
log(f"[+] Ransom note: {note}")

result = {
    "files_encrypted": encrypted, "ransom_note_created": True,
    "shadow_copies_deleted": True, "c2_callbacks": len(c2_hosts),
    "registry_modified": ["HKCU\\\\Run\\\\persist_malware"],
    "processes_spawned_suspicious": ["cmd.exe","vssadmin.exe","powershell.exe"],
    "network_connections_attempted": [
        {"ip":"185.220.101.47","port":443,"domain":"secure-payments.xyz"},
        {"ip":"91.108.4.200","port":8080},
    ],
    "records_exfiltrated": 0, "exfil_size_kb": 0,
}
print("\\nSANDBOX_RESULT_JSON:"+json.dumps(result), flush=True)
''',

"data_exfiltration": '''
import os, time, hashlib, socket, json, random
from pathlib import Path

ROOT = Path("/sandbox/exfil_data")
ROOT.mkdir(parents=True, exist_ok=True)

def log(msg): print(msg, flush=True)

log("[*] Data exfiltration payload initialising...")
log(f"[*] Host: {socket.gethostname()}  PID: {os.getpid()}")
time.sleep(0.2)

log("\\n[PHASE 1] Credential harvesting")
for t in ["/etc/passwd","~/.ssh/id_rsa","LSASS memory","HKLM/SAM","browser creds"]:
    log(f"[*] Probing: {t}"); time.sleep(0.08)
log("[+] Credentials harvested from 5 sources")

log("\\n[PHASE 2] Sensitive data collection")
records = [{"id":i,"cat":random.choice(["PII","Financial","IP","AuthToken"]),
            "val":hashlib.md5(os.urandom(8)).hexdigest()} for i in range(500)]
archive = ROOT / "exfil_package.json"
archive.write_text(json.dumps(records))
kb = round(archive.stat().st_size/1024, 1)
for i in range(0,500,100): log(f"[*] Collected {i+1} records..."); time.sleep(0.05)
log(f"[+] Archive: {kb} KB ({len(records)} records)")

log("\\n[PHASE 3] DNS tunnelling exfiltration")
c2 = "update.microsofft-cdn.com"
chunks = [records[i:i+50] for i in range(0,len(records),50)]
for idx,chunk in enumerate(chunks):
    enc = hashlib.sha256(str(chunk).encode()).hexdigest()[:16]
    log(f"[*] DNS: {enc}.{c2} (chunk {idx+1}/{len(chunks)})"); time.sleep(0.07)
log(f"[+] Exfil complete — {kb} KB via DNS tunnel")

log("\\n[PHASE 4] Covering tracks")
for l in ["Security.evtx","System.evtx","Application.evtx","PowerShell.evtx"]:
    log(f"[*] Clearing: {l}"); time.sleep(0.04)
log("[+] Event logs wiped")

result = {
    "files_encrypted": 0, "ransom_note_created": False,
    "shadow_copies_deleted": False, "c2_callbacks": len(chunks),
    "registry_modified": [], "processes_spawned_suspicious": ["powershell.exe","cmd.exe"],
    "network_connections_attempted": [
        {"ip":"185.220.101.47","port":443,"domain":c2},
        {"ip":"8.8.8.8","port":53,"domain":"dns-tunnel"},
    ],
    "records_exfiltrated": len(records), "exfil_size_kb": kb,
}
print("\\nSANDBOX_RESULT_JSON:"+json.dumps(result), flush=True)
''',
}

# ═══════════════════════════════════════════════════════════════════════════
# DOCKER RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def docker_available() -> bool:
    try:
        return subprocess.run(["docker","info"], capture_output=True,
                              timeout=5).returncode == 0
    except Exception:
        return False


def run_in_docker(incident_id: str, attack_type: str) -> dict:
    script = ATTACK_SCRIPTS.get(attack_type, ATTACK_SCRIPTS["ransomware"])

    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "payload.py"
        script_path.write_text(script, encoding="utf-8")

        # Pull image silently if missing
        if subprocess.run(["docker","image","inspect", DOCKER_IMAGE],
                          capture_output=True).returncode != 0:
            print(f"  [Docker] Pulling {DOCKER_IMAGE}...")
            subprocess.run(["docker","pull", DOCKER_IMAGE], check=True)

        cmd = [
            "docker","run","--rm",
            "--network","none",
            "--memory", DOCKER_MEM, "--cpus", DOCKER_CPUS,
            "--read-only",
            "--tmpfs","/sandbox:size=64m",
            "--tmpfs","/tmp:size=16m",
            "-v", f"{script_path}:/payload.py:ro",
            "--name", f"tl-{incident_id.lower()}-{int(time.time())}",
            DOCKER_IMAGE, "python", "/payload.py",
        ]

        print(f"  [Docker] Container launching ({DOCKER_IMAGE})...")
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            duration = round(time.time() - t0, 2)
        except subprocess.TimeoutExpired:
            return {"lines": ["[!] Container timed out"], "result": {}, "docker": True, "duration": 90}

    stdout = proc.stdout
    result_json = {}
    for line in stdout.splitlines():
        if line.startswith("SANDBOX_RESULT_JSON:"):
            try:
                result_json = json.loads(line[len("SANDBOX_RESULT_JSON:"):])
            except Exception:
                pass

    lines = [l for l in stdout.splitlines()
             if not l.startswith("SANDBOX_RESULT_JSON:")]
    print(f"  [Docker] ✓ Exited in {duration}s — {len(lines)} output lines")
    return {"lines": lines, "result": result_json, "docker": True, "duration": duration}


def run_subprocess_fallback(attack_type: str) -> dict:
    script = ATTACK_SCRIPTS.get(attack_type, ATTACK_SCRIPTS["ransomware"])
    with tempfile.TemporaryDirectory() as tmp:
        sp = Path(tmp) / "payload.py"
        sp.write_text(script, encoding="utf-8")
        t0 = time.time()
        proc = subprocess.run(["python", str(sp)], capture_output=True,
                              text=True, timeout=60, cwd=tmp)
        duration = round(time.time() - t0, 2)

    result_json = {}
    for line in proc.stdout.splitlines():
        if line.startswith("SANDBOX_RESULT_JSON:"):
            try:
                result_json = json.loads(line[len("SANDBOX_RESULT_JSON:"):])
            except Exception:
                pass

    lines = [l for l in proc.stdout.splitlines()
             if not l.startswith("SANDBOX_RESULT_JSON:")]
    return {"lines": lines, "result": result_json, "docker": False, "duration": duration}


# ═══════════════════════════════════════════════════════════════════════════
# EVIDENCE CAPTURE — camera frames from sandbox output
# ═══════════════════════════════════════════════════════════════════════════

_MITRE = {
    "ransomware":        [("Discovery","T1083"),("DefenseEva","T1490"),
                          ("Encrypt",  "T1486"),("C2",        "T1071")],
    "data_exfiltration": [("ValidAccts","T1078"),("Collection","T1560"),
                          ("Exfil-C2", "T1041"),("DNS-Tunnel","T1048")],
}
_BG     = (10,12,18);  _PANEL  = (16,20,30); _BORDER = (40,60,90)
_GREEN  = (0,230,80);  _RED    = (220,50,50); _ORANGE = (255,140,0)
_YELLOW = (240,200,40);_WHITE  = (220,225,235);_DIM   = (80,90,110)
_CYAN   = (0,200,220); _MAG    = (200,60,180)


def _line_color(line):
    l = line.lower()
    if "[phase" in l:                           return _CYAN
    if l.startswith("[+]"):                     return _GREEN
    if l.startswith("[!]") or "error" in l:     return _RED
    if "encrypt" in l or "locked" in l:         return _ORANGE
    if "exfil" in l or "dns" in l:              return _MAG
    if "beacon" in l or "c2" in l:              return _YELLOW
    if l.startswith("[*]"):                     return _WHITE
    return _DIM


def _bar(draw, x, y, w, h, pct, color):
    draw.rectangle([x, y, x+w, y+h], fill=(30,35,50))
    fw = int(w * min(pct, 1.0))
    if fw: draw.rectangle([x, y, x+fw, y+h], fill=color)
    draw.rectangle([x, y, x+w, y+h], outline=_BORDER, width=1)


def generate_sandbox_frame(idx, total, lines, incident_id, attack_type,
                            base_ts, out_path, behavioral_result,
                            verdict, confidence):
    if not PIL_AVAILABLE:
        out_path.write_bytes(b"PIL_UNAVAILABLE"); return

    W, H, TW = 1280, 720, 860
    img  = Image.new("RGB", (W, H), _BG)
    draw = ImageDraw.Draw(img)
    ts   = base_ts + timedelta(seconds=idx * 2)
    pct  = (idx + 1) / total

    # ── Top bar ──────────────────────────────────────────────────────────
    draw.rectangle([0, 0, W, 32], fill=(8,10,16))
    draw.rectangle([0, 32, W, 33], fill=_BORDER)
    draw.text((8, 8),
              f"  ◉ SANDBOX DETONATION  │  {incident_id}  │  "
              f"{attack_type.upper().replace('_',' ')}",
              fill=_GREEN)
    t_str = f"{idx*2//60:02d}:{idx*2%60:02d}  {ts.strftime('%H:%M:%S UTC')}  "
    draw.text((W - len(t_str)*7 - 4, 8), t_str, fill=_DIM)

    # ── Divider ───────────────────────────────────────────────────────────
    draw.rectangle([TW, 33, TW+1, H], fill=_BORDER)

    # ── Terminal (left) ───────────────────────────────────────────────────
    LH = 15; MAX = (H - 60) // LH
    visible_lines = lines[:int(len(lines)*pct)][-MAX:]
    for row, line in enumerate(visible_lines):
        draw.text((10, 40 + row*LH), line[:(TW-16)//7], fill=_line_color(line))
    if idx % 2 == 0 and visible_lines:
        cy = 40 + len(visible_lines)*LH
        draw.rectangle([10, cy+2, 16, cy+13], fill=_GREEN)

    # ── Right panel ───────────────────────────────────────────────────────
    px = TW + 10; py = 40

    def header(txt, y):
        draw.rectangle([TW+4, y, W-4, y+18], fill=(20,28,45))
        draw.text((px, y+2), txt, fill=_CYAN)
        return y + 22

    def row(label, val, y, vc=_WHITE):
        draw.text((px,      y), label, fill=_DIM)
        draw.text((px+130,  y), str(val), fill=vc)
        return y + 16

    # Status
    py = header("◈ DETONATION STATUS", py)
    sc = _RED if pct > 0.6 else _ORANGE if pct > 0.3 else _YELLOW
    py = row("Status",    "ACTIVE" if idx < total-1 else "COMPLETE", py, sc)
    py = row("Progress",  f"{pct:.0%}", py)
    py = row("Runtime",   f"{idx*2}s / {total*2}s", py)
    py = row("Container", "threatlens-sandbox", py)
    py = row("Image",     "python:3.11-slim", py)
    _bar(draw, px, py, W-px-8, 10, pct, sc); py += 18

    # Threat Metrics
    py = header("◈ THREAT METRICS", py)
    enc_total = behavioral_result.get("files_encrypted", 0)
    enc_now   = int(enc_total * pct)
    py = row("Files encrypted", f"{enc_now:,}", py, _RED if enc_now else _DIM)
    if enc_total:
        _bar(draw, px, py, W-px-8, 8, enc_now/max(enc_total,1), _RED); py += 14

    exfil = behavioral_result.get("exfil_size_kb", 0)
    py = row("Exfil KB",   f"{round(exfil*pct,1)}", py, _MAG if exfil else _DIM)
    c2   = behavioral_result.get("c2_callbacks", 0)
    py = row("C2 beacons", f"{int(c2*pct)}",        py, _YELLOW if c2 else _DIM)
    py = row("Shadows",
             "DELETED" if pct > 0.45 and behavioral_result.get("shadow_copies_deleted")
             else "intact",
             py, _RED if pct > 0.45 and behavioral_result.get("shadow_copies_deleted") else _GREEN)
    py = row("Ransom note",
             "DROPPED" if pct > 0.85 and behavioral_result.get("ransom_note_created")
             else "pending",
             py, _RED if pct > 0.85 and behavioral_result.get("ransom_note_created") else _DIM)
    py += 6

    # IOCs
    py = header("◈ INDICATORS OF COMPROMISE", py)
    ioc_strings = []
    for c in behavioral_result.get("network_connections_attempted", []):
        if c.get("ip"):     ioc_strings.append(f"IP: {c['ip']}")
        if c.get("domain"): ioc_strings.append(f"Domain: {c['domain']}")
    for rk in behavioral_result.get("registry_modified", []):
        ioc_strings.append(f"Reg: {rk}")
    for p in behavioral_result.get("processes_spawned_suspicious", []):
        ioc_strings.append(f"Proc: {p}")
    for ioc in ioc_strings[:6]:
        draw.text((px, py), f"• {ioc[:30]}", fill=_MAG); py += 14
    py += 4

    # MITRE
    py = header("◈ MITRE ATT&CK", py)
    for tactic, tid in _MITRE.get(attack_type, [])[:5]:
        draw.text((px,    py), tid,    fill=_ORANGE)
        draw.text((px+60, py), tactic, fill=_DIM); py += 14

    # ── Bottom bar ────────────────────────────────────────────────────────
    draw.rectangle([0, H-24, W, H], fill=(8,10,16))
    draw.rectangle([0, H-25, W, H-24], fill=_BORDER)
    draw.text((8, H-18), f"Frame {idx+1:03d}/{total:03d}", fill=_DIM)
    if verdict and confidence >= 70:
        draw.text((TW//2-50, H-18), f"VERDICT: {verdict}", fill=_RED)
        draw.text((W-200,    H-18), f"Confidence: {confidence}%", fill=_WHITE)

    img.save(out_path, "JPEG", quality=88)


# ═══════════════════════════════════════════════════════════════════════════
# NETWORK PCAP built from sandbox C2 connections
# ═══════════════════════════════════════════════════════════════════════════

def _pcap_header():
    return struct.pack("<IHHiIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)

def _eth_ip_tcp(src_ip, dst_ip, sport, dport, payload, ts):
    def ip2b(ip): return bytes(int(x) for x in ip.split("."))
    import random as _r
    tcp = struct.pack("!HHIIBBHHH", sport, dport, _r.randint(1,999999),
                      0, 0x50, 0x018, 65535, 0, 0)
    tot = 20 + 20 + len(payload)
    ip4 = struct.pack("!BBHHHBBH4s4s", 0x45, 0, tot,
                      _r.randint(1,65535), 0x4000, 64, 6, 0,
                      ip2b(src_ip), ip2b(dst_ip))
    eth = bytes([0x00,0x1A,0x2B,0x3C,0x4D,0x5E,
                 0x00,0x0C,0x29,0x6A,0x7B,0x8C,0x08,0x00])
    frame = eth + ip4 + tcp + payload
    sec   = int(ts.timestamp()); usec = ts.microsecond
    return struct.pack("<IIII", sec, usec, len(frame), len(frame)) + frame

def _eth_ip_udp(src_ip, dst_ip, sport, dport, payload, ts):
    def ip2b(ip): return bytes(int(x) for x in ip.split("."))
    import random as _r
    udp = struct.pack("!HHHH", sport, dport, 8+len(payload), 0)
    tot = 20 + 8 + len(payload)
    ip4 = struct.pack("!BBHHHBBH4s4s", 0x45, 0, tot,
                      _r.randint(1,65535), 0x4000, 64, 17, 0,
                      ip2b(src_ip), ip2b(dst_ip))
    eth = bytes([0x00,0x1A,0x2B,0x3C,0x4D,0x5E,
                 0x00,0x0C,0x29,0x6A,0x7B,0x8C,0x08,0x00])
    frame = eth + ip4 + udp + payload
    sec = int(ts.timestamp()); usec = ts.microsecond
    return struct.pack("<IIII", sec, usec, len(frame), len(frame)) + frame


def build_pcap_from_sandbox(behavioral_result: dict, base_ts: datetime,
                             attack_type: str) -> bytes:
    """Build a real binary PCAP from the sandbox's recorded C2 connections."""
    packets = [_pcap_header()]
    ts      = base_ts
    src_ip  = "172.17.0.2"   # typical Docker bridge IP

    conns = behavioral_result.get("network_connections_attempted", [])

    for conn in conns:
        dst_ip   = conn.get("ip",   "185.220.101.47")
        dst_port = conn.get("port", 443)
        domain   = conn.get("domain", "")
        sport    = 49000 + hash(dst_ip) % 10000

        # DNS lookup if domain present
        if domain:
            def dns_query(d):
                labels = b""
                for part in d.split("."):
                    labels += bytes([len(part)]) + part.encode()
                labels += b"\x00"
                return (struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) +
                        labels + struct.pack("!HH", 1, 1))
            ts += timedelta(milliseconds=80)
            packets.append(_eth_ip_udp(src_ip, "8.8.8.8", 54321, 53,
                                       dns_query(domain), ts))

        # TCP SYN → SYN-ACK → ACK
        for flags in (0x002, 0x012, 0x010):
            ts += timedelta(milliseconds=20)
            packets.append(_eth_ip_tcp(src_ip, dst_ip, sport, dst_port,
                                       b"", ts))

        # Data bursts (C2 traffic)
        if attack_type == "data_exfiltration":
            for _ in range(6):
                ts += timedelta(milliseconds=150)
                packets.append(_eth_ip_tcp(src_ip, dst_ip, sport, dst_port,
                                           os.urandom(4096 + hash(ts.microsecond) % 8192), ts))
        else:
            # Ransomware: key fetch + small beacon
            for payload in [os.urandom(512), os.urandom(256)]:
                ts += timedelta(milliseconds=100)
                packets.append(_eth_ip_tcp(src_ip, dst_ip, sport, dst_port,
                                           payload, ts))

        # SMB probes for ransomware lateral movement
        if attack_type == "ransomware":
            for last in [46, 47, 48]:
                ts += timedelta(milliseconds=40)
                smb = b"\x00\x00\x00\x2f\xff\x53\x4d\x42\x72" + os.urandom(40)
                packets.append(_eth_ip_tcp(src_ip, f"192.168.10.{last}",
                                           sport+1, 445, smb, ts))

    return b"".join(packets)


# ═══════════════════════════════════════════════════════════════════════════
# BEHAVIOUR CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════

def classify(log: dict):
    score = 0; indicators = []
    enc = log.get("files_encrypted", 0)
    if enc > 100: score += 40; indicators.append("mass_file_encryption")
    elif enc > 10: score += 25; indicators.append("file_encryption_detected")
    if log.get("ransom_note_created"):  score += 30; indicators.append("ransom_note_dropped")
    if log.get("shadow_copies_deleted"):score += 25; indicators.append("backup_destruction")
    conns = log.get("network_connections_attempted", [])
    if conns:
        score += 20; indicators.append("c2_callback")
        bad = {"secure-payments.xyz","update.microsofft-cdn.com","evil-c2.ru"}
        if any(c.get("domain") in bad for c in conns):
            score += 10; indicators.append("known_c2_domain")
    if log.get("registry_modified"):   score += 15; indicators.append("persistence")
    if log.get("processes_spawned_suspicious"): score += 10; indicators.append("suspicious_procs")
    if log.get("records_exfiltrated",0)>0: score += 35; indicators.append("data_exfiltration")
    if log.get("exfil_size_kb",0)>0:       score += 10; indicators.append("large_transfer")
    score = min(score, 100)
    verdict = "MALICIOUS" if score>=70 else "SUSPICIOUS" if score>=40 else "BENIGN"
    return verdict, score, indicators


# ═══════════════════════════════════════════════════════════════════════════
# SHA-256 MANIFEST
# ═══════════════════════════════════════════════════════════════════════════

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(incident_id: str, folder: Path, incident: dict,
                   verdict: str, score: int, iocs: dict) -> dict:
    file_records = []
    for fp in sorted(folder.rglob("*")):
        if fp.is_file():
            file_records.append({
                "path":        str(fp.relative_to(folder)),
                "size_bytes":  fp.stat().st_size,
                "sha256":      sha256_file(fp),
            })
    chain = hashlib.sha256(
        "".join(r["sha256"] for r in file_records).encode()
    ).hexdigest()
    total_mb = round(sum(r["size_bytes"] for r in file_records) / (1024*1024), 3)

    return {
        "schema_version":    "2.1",
        "incident_id":       incident_id,
        "capture_timestamp": datetime.utcnow().isoformat() + "Z",
        "captured_by":       "ThreatLens Sandbox+Evidence Engine v2.0",
        "incident_metadata": {
            "severity":    incident["severity"],
            "risk_score":  incident["risk_score"],
            "attack_type": incident["attack_type"],
            "zone":        incident.get("zone", "sandbox"),
            "verdict":     verdict,
            "confidence":  score,
            "indicators":  incident.get("indicators", []),
        },
        "iocs":              iocs,
        "evidence_files":    file_records,
        "file_count":        len(file_records),
        "total_size_mb":     total_mb,
        "integrity": {
            "sha256_chain_hash": chain,
            "algorithm":         "SHA-256",
            "tamper_evident":    True,
        },
        "blockchain_anchor": {
            "status":   "PENDING",
            "network":  "Ethereum Sepolia Testnet",
            "contract": "0x742d35Cc6634C0532925a3b8D4C9fA1234567890",
            "tx_hash":  None,
        },
        "ready_for_blockchain": True,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

async def process(incident: dict) -> dict:
    inc_id      = incident["incident_id"]
    attack_type = incident["attack_type"]
    base_ts     = datetime.utcnow()

    folder      = EVIDENCE_ROOT / inc_id
    cam_folder  = folder / "camera"
    net_folder  = folder / "network"
    log_folder  = folder / "logs"
    files_folder= folder / "files"
    for d in (cam_folder, net_folder, log_folder, files_folder):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n  📁 Evidence root: {folder}")

    # ── Step 1: Detonate in Docker ────────────────────────────────────────
    print("  🐳 Detonating in sandbox...")
    if docker_available():
        execution = run_in_docker(inc_id, attack_type)
    else:
        print("  [Docker] ⚠ Falling back to subprocess sandbox")
        execution = run_subprocess_fallback(attack_type)

    output_lines    = execution["lines"]
    behavioral_log  = execution["result"]
    verdict, score, indicators = classify(behavioral_log)
    print(f"  🔬 Verdict: {verdict}  Score: {score}  "
          f"Indicators: {len(indicators)}")

    # ── Step 2: Camera — PIL frames of the sandbox execution ─────────────
    if PIL_AVAILABLE:
        print(f"  🎥 Generating {NUM_FRAMES} sandbox evidence frames...")
        for i in range(NUM_FRAMES):
            generate_sandbox_frame(
                idx=i, total=NUM_FRAMES, lines=output_lines,
                incident_id=inc_id, attack_type=attack_type,
                base_ts=base_ts,
                out_path=cam_folder / f"frame_{i:04d}.jpg",
                behavioral_result=behavioral_log,
                verdict=verdict, confidence=score,
            )
        print(f"    ✓ {NUM_FRAMES} frames written")

    # ── Step 3: Network — real PCAP from sandbox C2 connections ──────────
    print("  🌐 Building network PCAP from sandbox C2 traffic...")
    pcap_data = build_pcap_from_sandbox(behavioral_log, base_ts, attack_type)
    pcap_path = net_folder / "capture.pcap"
    pcap_path.write_bytes(pcap_data)
    print(f"    ✓ PCAP: {len(pcap_data):,} bytes")

    # ── Step 4: Logs — structured events from sandbox stdout + IOCs ───────
    print("  📋 Writing structured log evidence...")
    ioc_list = []
    for c in behavioral_log.get("network_connections_attempted", []):
        if c.get("ip"):     ioc_list.append({"type":"ip",     "value":c["ip"]})
        if c.get("domain"): ioc_list.append({"type":"domain", "value":c["domain"]})
    for rk in behavioral_log.get("registry_modified", []):
        ioc_list.append({"type":"registry", "value":rk})

    iocs_dict = {
        "ips":     [c["ip"]     for c in behavioral_log.get("network_connections_attempted",[]) if c.get("ip")],
        "domains": [c["domain"] for c in behavioral_log.get("network_connections_attempted",[]) if c.get("domain")],
        "registry_keys":    behavioral_log.get("registry_modified", []),
        "processes":        behavioral_log.get("processes_spawned_suspicious", []),
        "mitre_behaviors":  list({
            t for cond, t in [
                (behavioral_log.get("files_encrypted",0)>0,       "T1486"),
                (behavioral_log.get("shadow_copies_deleted"),      "T1490"),
                (behavioral_log.get("network_connections_attempted"),"T1071"),
                (behavioral_log.get("registry_modified"),          "T1547"),
                (behavioral_log.get("records_exfiltrated",0)>0,    "T1041"),
            ] if cond
        }),
    }

    log_bundle = {
        "incident_id":       inc_id,
        "source":            "ThreatLens Sandbox (Docker)",
        "attack_type":       attack_type,
        "detonation_ts":     base_ts.isoformat() + "Z",
        "container_image":   "python:3.11-slim",
        "docker_used":       execution["docker"],
        "duration_sec":      execution["duration"],
        "behavioral_summary": behavioral_log,
        "verdict":           verdict,
        "confidence_score":  score,
        "indicators":        indicators,
        "iocs":              ioc_list,
        "terminal_output":   output_lines,
        "line_count":        len(output_lines),
    }
    (log_folder / "sandbox_log.json").write_text(
        json.dumps(log_bundle, indent=2), encoding="utf-8")
    (log_folder / "terminal_output.log").write_text(
        "\n".join(output_lines), encoding="utf-8")
    print(f"    ✓ {len(output_lines)} terminal lines, "
          f"{len(ioc_list)} IOCs logged")

    # ── Step 5: Files — artifacts produced by the malware ─────────────────
    print("  🔒 Capturing malware file artifacts...")
    enc_count = behavioral_log.get("files_encrypted", 0)
    exfil_kb  = behavioral_log.get("exfil_size_kb", 0)

    if enc_count > 0:
        # Reproduce a small set of encrypted artifacts for evidence
        xor_key = 0xDE
        sample_files = [
            ("financial_report_Q4.xlsx", b"PK\x03\x04" + b"Mock Excel data " * 200),
            ("customer_records.csv",
             ("id,name,email,ssn\n" + "\n".join(
                 f"{i},User{i},u{i}@corp.com,{i:09d}" for i in range(200)
             )).encode()),
            ("backup_credentials.txt",
             b"Server: db01.corp\nUser: sa\nPass: P@ssw0rd!\n"),
        ]
        for fname, content in sample_files:
            (files_folder / fname).write_bytes(content)
            enc = bytes(b ^ xor_key for b in content)
            (files_folder / (fname + ".locked")).write_bytes(enc)

        ransom_note = (
            f"INCIDENT: {inc_id}\n"
            f"FILES ENCRYPTED: {enc_count}\n"
            f"ENCRYPTION: AES-256-CBC\n"
            f"PAYMENT: 4.5 BTC\n"
            f"DEADLINE: 72h\n"
            f"[ThreatLens Demo — Simulated Evidence]\n"
        )
        (files_folder / "README_RESTORE.txt").write_text(
            ransom_note, encoding="utf-8")
        print(f"    ✓ {len(sample_files)} encrypted file pairs + ransom note")

    elif exfil_kb > 0:
        records = [{"id":i,"category":"PII","value":hashlib.md5(
            str(i).encode()).hexdigest()} for i in range(200)]
        (files_folder / "exfiltrated_records_sample.json").write_text(
            json.dumps(records[:50], indent=2), encoding="utf-8")
        print(f"    ✓ Exfil sample written ({exfil_kb} KB total in sandbox)")

    # ── Step 6: Threat timeline ───────────────────────────────────────────
    print("  🗺️  Reconstructing threat timeline...")
    phase_map = {
        "ransomware": [
            (0,   "Initial Access",      "RDP brute-force → admin credentials compromised"),
            (15,  "Execution",           "Ransomware binary dropped and executed in sandbox"),
            (30,  "Discovery",           f"File system enumeration — {enc_count} files targeted"),
            (50,  "Defense Evasion",     "Shadow copies deleted, backup services stopped"),
            (70,  "C2 Communication",    f"{behavioral_log.get('c2_callbacks',0)} beacons to attacker infrastructure"),
            (90,  "Impact: Encryption",  f"{enc_count} files encrypted with .locked extension"),
            (110, "Impact: Ransom Note", "README_RESTORE.txt dropped in target directories"),
        ],
        "data_exfiltration": [
            (0,   "Initial Access",      "Phishing → credential harvest → initial foothold"),
            (20,  "Discovery",           "Internal network scan, credential enumeration"),
            (40,  "Collection",          f"{behavioral_log.get('records_exfiltrated',0)} records staged for exfiltration"),
            (60,  "C2 Setup",            "DNS tunnel established to attacker infrastructure"),
            (80,  "Exfiltration",        f"{exfil_kb} KB exfiltrated via DNS tunnelling"),
            (100, "Defense Evasion",     "Event logs cleared, traces removed"),
        ],
    }
    timeline = [
        {
            "phase":       phase,
            "timestamp":   (base_ts + timedelta(seconds=delta)).isoformat() + "Z",
            "delta_sec":   delta,
            "description": desc,
            "confidence":  round(0.85 + hash(phase) % 10 * 0.01, 2),
        }
        for delta, phase, desc in phase_map.get(attack_type, [])
    ]
    (folder / "threat_timeline.json").write_text(
        json.dumps({
            "incident_id":   inc_id,
            "attack_type":   attack_type,
            "kill_chain":    "MITRE ATT&CK v14",
            "total_duration_sec": phase_map.get(attack_type, [[120]])[-1][0],
            "timeline":      timeline,
        }, indent=2), encoding="utf-8")
    print(f"    ✓ {len(timeline)} kill-chain phases")

    # ── Step 7: Metadata ──────────────────────────────────────────────────
    (folder / "metadata.json").write_text(json.dumps({
        "incident_id":  inc_id,
        "risk_score":   incident["risk_score"],
        "severity":     incident["severity"],
        "attack_type":  attack_type,
        "verdict":      verdict,
        "confidence":   score,
        "zone":         incident.get("zone","sandbox"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "engine":       "ThreatLens Sandbox+Evidence v2.0",
    }, indent=2), encoding="utf-8")

    # ── Step 8: Manifest ──────────────────────────────────────────────────
    print("  📄 Building integrity manifest...")
    manifest = build_manifest(inc_id, folder, incident, verdict, score, iocs_dict)
    manifest_path = folder / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"    ✓ {manifest['file_count']} files, "
          f"{manifest['total_size_mb']} MB, "
          f"chain: {manifest['integrity']['sha256_chain_hash'][:20]}...")

    return manifest


# ═══════════════════════════════════════════════════════════════════════════
# TEST INCIDENTS
# ═══════════════════════════════════════════════════════════════════════════

TEST_INCIDENTS = [
    {
        "incident_id": "INC-TEST-RANSOMWARE",
        "risk_score":  95.0,
        "severity":    "CRITICAL",
        "attack_type": "ransomware",
        "zone":        "internal_network",
        "file_hash":   "sha256:4a8b2c1d9e3f0a7b6c5d4e3f2a1b0c9d",
    },
    {
        "incident_id": "INC-TEST-EXFIL",
        "risk_score":  87.5,
        "severity":    "HIGH",
        "attack_type": "data_exfiltration",
        "zone":        "server_room",
        "file_hash":   "sha256:1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f",
    },
]


async def main():
    print("\n" + "═" * 80)
    print("  THREATLENS — SANDBOX + EVIDENCE CAPTURE (COMBINED DEMO)")
    print("═" * 80)
    print(f"\n  Evidence root : {EVIDENCE_ROOT}")
    print(f"  PIL           : {'✓ AVAILABLE' if PIL_AVAILABLE else '✗ NOT FOUND (pip install pillow)'}")
    print(f"  Docker        : {'✓ RUNNING' if docker_available() else '⚠ NOT AVAILABLE (subprocess fallback)'}")
    print(f"  Incidents     : {len(TEST_INCIDENTS)}\n")

    results = []
    for incident in TEST_INCIDENTS:
        inc_id = incident["incident_id"]
        atype  = incident["attack_type"]
        print(f"\n{'─'*80}")
        print(f"  ▶ {inc_id}  [{atype.upper().replace('_',' ')}]  "
              f"Risk: {incident['risk_score']}")
        print(f"{'─'*80}")
        t0 = time.time()
        try:
            manifest = await process(incident)
            elapsed  = time.time() - t0
            results.append((inc_id, True, manifest, elapsed))
            print(f"\n  ✅ Complete in {elapsed:.1f}s")
        except Exception as e:
            import traceback; traceback.print_exc()
            results.append((inc_id, False, str(e), time.time()-t0))

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'═'*80}")
    print("  📊  SUMMARY")
    print(f"{'═'*80}\n")

    ok = sum(1 for _,s,*_ in results if s)
    print(f"  Processed: {ok}/{len(results)} incidents\n")

    for inc_id, success, data, elapsed in results:
        if success:
            m = data
            f = EVIDENCE_ROOT / inc_id
            print(f"  ✅  {inc_id}")
            print(f"      Files:       {m['file_count']}")
            print(f"      Size:        {m['total_size_mb']} MB")
            print(f"      Verdict:     {m['incident_metadata']['verdict']}  "
                  f"({m['incident_metadata']['confidence']}%)")
            print(f"      Indicators:  {', '.join(m['incident_metadata']['indicators'])}")
            print(f"      Chain hash:  {m['integrity']['sha256_chain_hash'][:32]}...")
            print(f"      Duration:    {elapsed:.1f}s")
            print(f"      Path:        {f}")
            print()

            print(f"      Evidence tree:")
            for fp in sorted(f.rglob("*")):
                if fp.is_file():
                    print(f"        ├─ {fp.relative_to(f)}  "
                          f"({fp.stat().st_size:,} bytes)")
            print()
        else:
            print(f"  ❌  {inc_id}: {data}\n")

    print("═" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())