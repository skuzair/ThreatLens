"""
Enhanced Evidence Capture Demo - Realistic Forensic Artifacts
=============================================================
Generates real binary files that look like actual captured evidence:
  - Annotated camera frames (real JPEG with bounding boxes + threat labels)
  - Realistic PCAP files (valid binary packet capture format)
  - Rich structured log bundles (JSON with IOCs, MITRE ATT&CK tags)
  - Ransomware file artifacts (XOR-encrypted files with ransom note)
  - SHA256-chained evidence manifests
  - Full threat timeline reconstruction

Run from ThreatLens root:
    python demo_evidence_enhanced.py
"""

import asyncio
import hashlib
import json
import os
import struct
import sys
import time
import random
import io
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[!] Pillow not found — camera frames will be skipped. Run: pip install pillow")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
os.environ["ENABLE_KAFKA"] = "false"
EVIDENCE_ROOT = Path(__file__).parent / "evidence"
EVIDENCE_ROOT.mkdir(exist_ok=True)

SEED = 42
random.seed(SEED)

# MITRE ATT&CK technique catalogue used in this demo
MITRE_TECHNIQUES = {
    "data_exfiltration": [
        {"id": "T1041", "name": "Exfiltration Over C2 Channel"},
        {"id": "T1048", "name": "Exfiltration Over Alternative Protocol"},
        {"id": "T1078", "name": "Valid Accounts"},
        {"id": "T1560", "name": "Archive Collected Data"},
    ],
    "ransomware": [
        {"id": "T1486", "name": "Data Encrypted for Impact"},
        {"id": "T1490", "name": "Inhibit System Recovery"},
        {"id": "T1489", "name": "Service Stop"},
        {"id": "T1083", "name": "File and Directory Discovery"},
    ],
    "lateral_movement": [
        {"id": "T1021", "name": "Remote Services"},
        {"id": "T1075", "name": "Pass the Hash"},
        {"id": "T1076", "name": "Remote Desktop Protocol"},
    ],
}

# =============================================================================
# 1. CAMERA EVIDENCE  — Real JPEG with drawn bounding boxes
# =============================================================================

def _random_person_color():
    palettes = [
        (220, 50, 50),   # red-flagged
        (255, 140, 0),   # orange-warning
        (50, 180, 80),   # green-normal
    ]
    return random.choice(palettes)


def generate_camera_frame(incident_type: str, incident_id: str, frame_index: int, ts: datetime):
    """Draw a realistic surveillance-style annotated frame."""
    if not PIL_AVAILABLE:
        return None

    W, H = 1280, 720

    # Dark surveillance background
    img = Image.new("RGB", (W, H), color=(15, 15, 20))
    draw = ImageDraw.Draw(img)

    # Grid overlay (CCTV feel)
    for x in range(0, W, 64):
        draw.line([(x, 0), (x, H)], fill=(25, 25, 35), width=1)
    for y in range(0, H, 64):
        draw.line([(0, y), (W, y)], fill=(25, 25, 35), width=1)

    # Simulate background scene elements
    # Server racks
    for rx in [100, 300, 500, 700, 900, 1100]:
        rh = random.randint(300, 500)
        ry = H - rh - 50
        draw.rectangle([rx, ry, rx + 60, H - 50], fill=(30, 30, 45), outline=(60, 60, 80))
        # Rack lights
        for ly in range(ry + 20, H - 60, 30):
            color = random.choice([(0, 200, 0), (0, 200, 0), (200, 0, 0), (200, 200, 0)])
            draw.ellipse([rx + 10, ly, rx + 20, ly + 10], fill=color)

    # Floor line
    draw.line([(0, H - 50), (W, H - 50)], fill=(60, 60, 80), width=3)

    # ---- Detected persons ----
    persons = []
    num_persons = 2 if incident_type == "data_exfiltration" else 1
    for i in range(num_persons):
        x1 = random.randint(150, 900)
        y1 = random.randint(200, 420)
        bw = random.randint(80, 120)
        bh = random.randint(180, 260)
        x2, y2 = x1 + bw, y1 + bh
        threat_level = "HIGH" if i == 0 else "MEDIUM"
        color = (220, 50, 50) if threat_level == "HIGH" else (255, 140, 0)
        confidence = round(random.uniform(0.87, 0.99), 2)
        persons.append({"box": (x1, y1, x2, y2), "color": color,
                        "threat": threat_level, "conf": confidence, "id": f"P{i+1:02d}"})

    for p in persons:
        x1, y1, x2, y2 = p["box"]
        # Silhouette
        draw.rectangle([x1+10, y1+30, x2-10, y2], fill=(50, 50, 70))
        draw.ellipse([x1+15, y1, x2-15, y1+50], fill=(80, 60, 50))
        # Bounding box
        draw.rectangle([x1, y1, x2, y2], outline=p["color"], width=3)
        # Corner accents
        for cx, cy, dx, dy in [(x1, y1, 1, 1), (x2, y1, -1, 1),
                                (x1, y2, 1, -1), (x2, y2, -1, -1)]:
            draw.line([(cx, cy), (cx + dx*20, cy)], fill=p["color"], width=3)
            draw.line([(cx, cy), (cx, cy + dy*20)], fill=p["color"], width=3)
        # Label background
        label = f"{p['id']} [{p['threat']}] {p['conf']:.0%}"
        lx, ly = x1, y1 - 22
        draw.rectangle([lx, ly, lx + len(label)*8 + 8, ly + 20], fill=p["color"])
        draw.text((lx + 4, ly + 2), label, fill=(255, 255, 255))

    # ---- Threat zone highlight ----
    zone_x1, zone_y1, zone_x2, zone_y2 = 80, 150, 760, H - 50
    for i in range(3):
        alpha_rect = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ad = ImageDraw.Draw(alpha_rect)
        ad.rectangle([zone_x1 - i*2, zone_y1 - i*2, zone_x2 + i*2, zone_y2 + i*2],
                     outline=(220, 50, 50, max(80 - i*25, 20)), width=2)
        img = Image.alpha_composite(img.convert("RGBA"), alpha_rect).convert("RGB")
        draw = ImageDraw.Draw(img)

    draw.text((zone_x1 + 4, zone_y1 + 4), "⚠ RESTRICTED ZONE BREACH", fill=(220, 50, 50))

    # ---- HUD overlay ----
    # Top bar
    draw.rectangle([0, 0, W, 40], fill=(10, 10, 15))
    cam_id = f"CAM-{random.randint(1, 16):02d}"
    draw.text((10, 10), f"● REC  {cam_id}  ZONE: SERVER_ROOM", fill=(220, 50, 50))
    draw.text((W - 280, 10), ts.strftime("%Y-%m-%d  %H:%M:%S UTC"), fill=(180, 180, 200))

    # Bottom bar
    draw.rectangle([0, H - 30, W, H], fill=(10, 10, 15))
    draw.text((10, H - 22), f"INCIDENT: {incident_id}  |  FRAME: {frame_index:04d}  |  THREAT: ACTIVE", fill=(220, 180, 0))

    # Scan-line effect
    for y in range(0, H, 4):
        draw.line([(0, y), (W, y)], fill=(0, 0, 0, 20), width=1)

    # Threat type banner
    threat_label = incident_type.upper().replace("_", " ")
    draw.rectangle([W - 320, 50, W, 90], fill=(180, 20, 20))
    draw.text((W - 310, 58), f"THREAT: {threat_label}", fill=(255, 255, 255))

    return img


def generate_video_clip_frames(folder: Path, incident_type: str, incident_id: str,
                                base_ts: datetime, num_frames: int = 5):
    """Generate a sequence of annotated frames and a basic MJPEG-style clip."""
    frames = []
    for i in range(num_frames):
        ts = base_ts + timedelta(seconds=i * 2)
        img = generate_camera_frame(incident_type, incident_id, i, ts)
        if img is None:
            continue
        fp = folder / f"frame_{i:04d}_annotated.jpg"
        img.save(fp, "JPEG", quality=88)
        frames.append(fp)

    # Composite thumbnail (first frame = keyframe)
    if frames:
        keyframe = folder / "frame_keyframe_annotated.jpg"
        frames[0].rename(keyframe) if False else None  # keep originals
        # create a clip.mp4 placeholder with real JPEG data embedded
        clip_path = folder / "clip.mp4"
        with open(clip_path, "wb") as f:
            # Write a minimal MP4-style container header (ftyp box)
            ftyp = b'\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isomiso2'
            f.write(ftyp)
            # Append all frame JPEG data as mdat
            for fp in frames:
                f.write(fp.read_bytes())
        print(f"    ✓ {len(frames)} annotated frames + clip ({clip_path.stat().st_size/1024:.1f} KB)")

    return frames


# =============================================================================
# 2. NETWORK EVIDENCE — Real binary PCAP
# =============================================================================

def _pcap_global_header():
    """Standard libpcap global header (little-endian, Ethernet link type)."""
    return struct.pack("<IHHiIII",
                       0xa1b2c3d4,   # magic number
                       2, 4,          # version major/minor
                       0,             # timezone offset
                       0,             # timestamp accuracy
                       65535,         # snaplen
                       1)             # link type = Ethernet


def _pcap_packet(ts_sec, ts_usec, data: bytes):
    """Wrap raw bytes in a PCAP packet record."""
    return struct.pack("<IIII", ts_sec, ts_usec, len(data), len(data)) + data


def _eth_ip_tcp(src_ip, dst_ip, src_port, dst_port, payload: bytes,
                flags=0x018):  # PSH+ACK
    """Build a minimal Ethernet + IPv4 + TCP frame."""
    def ip_to_bytes(ip):
        return bytes(int(x) for x in ip.split("."))

    # TCP header (no options)
    tcp = struct.pack("!HHIIBBHHH",
                      src_port, dst_port,
                      random.randint(100000, 999999),  # seq
                      0,                               # ack
                      0x50,                            # data offset (5 * 4 = 20 bytes)
                      flags,
                      65535,                           # window
                      0, 0)                            # checksum (0=unchecked), urgent

    # IPv4 header
    total_len = 20 + 20 + len(payload)
    ipv4 = struct.pack("!BBHHHBBH4s4s",
                       0x45, 0,              # version+IHL, DSCP
                       total_len,
                       random.randint(1, 65535),  # id
                       0x4000,               # don't fragment
                       64,                  # TTL
                       6,                   # protocol TCP
                       0,                   # checksum (unchecked)
                       ip_to_bytes(src_ip),
                       ip_to_bytes(dst_ip))

    # Ethernet header (fake MACs)
    eth = bytes([0x00, 0x1A, 0x2B, 0x3C, 0x4D, 0x5E,
                 0x00, 0x0C, 0x29, 0x6A, 0x7B, 0x8C,
                 0x08, 0x00])               # EtherType = IPv4

    return eth + ipv4 + tcp + payload


def _dns_query(domain: str):
    """Build a minimal DNS query packet (UDP payload only)."""
    labels = b""
    for part in domain.split("."):
        labels += bytes([len(part)]) + part.encode()
    labels += b"\x00"
    return (struct.pack("!HHHHHH",
                        random.randint(1, 65535),  # txid
                        0x0100,                    # flags: standard query
                        1, 0, 0, 0) +              # QDCOUNT=1
            labels +
            struct.pack("!HH", 1, 1))              # QTYPE=A, QCLASS=IN


def _eth_ip_udp(src_ip, dst_ip, src_port, dst_port, payload: bytes):
    def ip_to_bytes(ip):
        return bytes(int(x) for x in ip.split("."))
    udp = struct.pack("!HHHH", src_port, dst_port, 8 + len(payload), 0)
    total_len = 20 + 8 + len(payload)
    ipv4 = struct.pack("!BBHHHBBH4s4s",
                       0x45, 0, total_len,
                       random.randint(1, 65535), 0x4000, 64, 17, 0,
                       ip_to_bytes(src_ip), ip_to_bytes(dst_ip))
    eth = bytes([0x00, 0x1A, 0x2B, 0x3C, 0x4D, 0x5E,
                 0x00, 0x0C, 0x29, 0x6A, 0x7B, 0x8C, 0x08, 0x00])
    return eth + ipv4 + udp + payload


def generate_pcap(incident_type: str, base_ts: datetime) -> bytes:
    """Generate a realistic PCAP with scenario-appropriate traffic."""
    ts = base_ts
    packets = [_pcap_global_header()]

    internal_ip = "192.168.10.45"
    c2_ip = "185.220.101.47"          # Tor exit node range
    dns_server = "8.8.8.8"
    local_gw = "192.168.10.1"

    def add_pkt(data, delta_ms=50):
        nonlocal ts
        ts += timedelta(milliseconds=delta_ms + random.randint(0, 30))
        sec = int(ts.timestamp())
        usec = ts.microsecond
        packets.append(_pcap_packet(sec, usec, data))

    if incident_type == "data_exfiltration":
        # 1) DNS lookup for C2 domain
        c2_domain = "update.microsofft-cdn.com"   # typosquat
        dns_q = _eth_ip_udp(internal_ip, dns_server, 54321, 53, _dns_query(c2_domain))
        add_pkt(dns_q, 0)

        # 2) DNS response
        dns_r = _eth_ip_udp(dns_server, internal_ip, 53, 54321,
                             _dns_query(c2_domain) + struct.pack("!HH", 0xC00C, 1) +
                             struct.pack("!HHI", 1, 4, 300) +
                             bytes([185, 220, 101, 47]))
        add_pkt(dns_r, 20)

        # 3) TCP SYN to C2
        add_pkt(_eth_ip_tcp(internal_ip, c2_ip, 49152, 443, b"", 0x002), 80)
        # 4) SYN-ACK
        add_pkt(_eth_ip_tcp(c2_ip, internal_ip, 443, 49152, b"", 0x012), 15)
        # 5) ACK
        add_pkt(_eth_ip_tcp(internal_ip, c2_ip, 49152, 443, b"", 0x010), 5)

        # 6) TLS ClientHello
        tls_hello = bytes([0x16, 0x03, 0x01]) + struct.pack("!H", 512) + os.urandom(512)
        add_pkt(_eth_ip_tcp(internal_ip, c2_ip, 49152, 443, tls_hello), 10)

        # 7) Large data upload bursts (exfil)
        for chunk_i in range(8):
            chunk = os.urandom(random.randint(8192, 32768))  # 8–32 KB per burst
            add_pkt(_eth_ip_tcp(internal_ip, c2_ip, 49152, 443, chunk), 200)

        # 8) Some legitimate background traffic (cover)
        for _ in range(5):
            add_pkt(_eth_ip_tcp(internal_ip, "93.184.216.34", 55000, 80,
                                b"GET /favicon.ico HTTP/1.1\r\nHost: example.com\r\n\r\n"), 300)

    elif incident_type == "ransomware":
        c2_ransomware = "91.108.4.200"   # Telegram-adjacent IP used by Conti

        # 1) C2 beacon
        beacon = b"POST /api/register HTTP/1.1\r\nHost: secure-payments.xyz\r\n" \
                 b"User-Agent: Mozilla/5.0\r\nContent-Length: 128\r\n\r\n" + os.urandom(128)
        add_pkt(_eth_ip_tcp(internal_ip, c2_ransomware, 49200, 80, beacon), 0)

        # 2) Key exchange
        for _ in range(3):
            add_pkt(_eth_ip_tcp(c2_ransomware, internal_ip, 80, 49200,
                                os.urandom(random.randint(256, 1024))), 100)

        # 3) SMB lateral movement probes
        for host_last in [46, 47, 48, 49, 50]:
            target_ip = f"192.168.10.{host_last}"
            smb_probe = b"\x00\x00\x00\x2f\xff\x53\x4d\x42\x72" + os.urandom(40)
            add_pkt(_eth_ip_tcp(internal_ip, target_ip, 49300, 445, smb_probe), 50)

        # 4) Volume Shadow Copy deletion traffic (WMI/RPC)
        wmi_traffic = b"\x05\x00\x0b\x03" + os.urandom(200)
        add_pkt(_eth_ip_tcp(internal_ip, local_gw, 49400, 135, wmi_traffic), 200)

        # 5) Ransom note HTTP fetch
        ransom_req = b"GET /README_RESTORE.html HTTP/1.1\r\nHost: secure-payments.xyz\r\n\r\n"
        add_pkt(_eth_ip_tcp(internal_ip, c2_ransomware, 49500, 80, ransom_req), 500)

    else:
        # Generic suspicious traffic
        for _ in range(20):
            payload = os.urandom(random.randint(64, 512))
            add_pkt(_eth_ip_tcp(internal_ip, c2_ip, random.randint(49000, 65000),
                                random.choice([80, 443, 8080]), payload), 100)

    return b"".join(packets)


# =============================================================================
# 3. LOG EVIDENCE — Rich JSON with IOCs and MITRE tags
# =============================================================================

def generate_log_bundle(incident_type: str, incident_id: str, base_ts: datetime) -> dict:
    """Generate realistic structured log events."""
    techniques = MITRE_TECHNIQUES.get(incident_type, MITRE_TECHNIQUES["data_exfiltration"])

    events = []
    ts = base_ts

    if incident_type == "data_exfiltration":
        sequence = [
            ("AUTH",    "WARN",  "Failed sudo attempt: user 'svc_backup' → NOPASSWD escalation", "192.168.10.45", "T1078"),
            ("FILE",    "WARN",  "Mass file access: /data/customer_records/ — 2,847 files in 12s", "192.168.10.45", "T1560"),
            ("PROC",    "HIGH",  "Suspicious process: 7z.exe compressing /data → C:\\Temp\\arch.7z", "192.168.10.45", "T1560"),
            ("NET",     "CRIT",  "Outbound TCP:443 to 185.220.101.47 (Tor exit) — 47.3 MB transferred", "192.168.10.45", "T1041"),
            ("NET",     "HIGH",  "DNS query: update.microsofft-cdn.com (typosquat detected)", "192.168.10.45", "T1048"),
            ("DLP",     "CRIT",  "Data Loss Prevention: 47,392 records exfiltrated (PII detected)", "192.168.10.45", "T1041"),
            ("AUTH",    "HIGH",  "Account 'svc_backup' logged off — session duration: 00:02:31", "192.168.10.45", "T1078"),
        ]
    elif incident_type == "ransomware":
        sequence = [
            ("PROC",    "HIGH",  "New process: powershell.exe -enc JAB... (obfuscated payload)", "192.168.10.45", "T1083"),
            ("FILE",    "CRIT",  "Shadow copy deletion: vssadmin delete shadows /all /quiet", "192.168.10.45", "T1490"),
            ("SVC",     "CRIT",  "Service stopped: Windows Backup (wbengine), SQL Server (MSSQLSERVER)", "192.168.10.45", "T1489"),
            ("FILE",    "CRIT",  "Mass file encryption: 1,247 files renamed *.locked in /Users/shared", "192.168.10.45", "T1486"),
            ("NET",     "HIGH",  "C2 beacon: POST /api/register to 91.108.4.200 — key exchange detected", "192.168.10.45", "T1041"),
            ("FILE",    "HIGH",  "Ransom note dropped: README_RESTORE.html in 23 directories", "192.168.10.45", "T1486"),
            ("PROC",    "CRIT",  "Self-deletion: ransomware binary attempting to remove itself", "192.168.10.45", "T1027"),
        ]
    else:
        sequence = [
            ("NET",     "HIGH",  "Unusual lateral movement detected across subnet", "192.168.10.45", "T1021"),
        ]

    for i, (source, severity, message, src_ip, technique_id) in enumerate(sequence):
        ts += timedelta(seconds=random.randint(8, 45))
        technique = next((t for t in techniques if t["id"] == technique_id),
                         {"id": technique_id, "name": "Unknown"})
        events.append({
            "event_id": f"{incident_id}-LOG-{i+1:04d}",
            "timestamp": ts.isoformat() + "Z",
            "source": source,
            "severity": severity,
            "message": message,
            "host": "SRV-DC01.corp.local",
            "source_ip": src_ip,
            "user": "svc_backup" if i < 3 else "SYSTEM",
            "process": random.choice(["powershell.exe", "cmd.exe", "svchost.exe", "7z.exe"]),
            "pid": random.randint(1000, 9999),
            "mitre_attack": {
                "technique_id": technique["id"],
                "technique_name": technique["name"],
                "tactic": "exfiltration" if incident_type == "data_exfiltration" else "impact",
            },
            "ioc_matches": _generate_iocs(incident_type),
            "raw": f"[{ts.strftime('%Y-%m-%dT%H:%M:%SZ')}] [{severity}] {source}: {message}"
        })

    ioc_summary = {
        "malicious_ips": ["185.220.101.47", "91.108.4.200"] if incident_type == "ransomware"
                          else ["185.220.101.47"],
        "malicious_domains": ["update.microsofft-cdn.com"],
        "malicious_hashes": [hashlib.sha256(os.urandom(32)).hexdigest()],
        "threat_actor": "APT-SHADOW-21" if incident_type == "data_exfiltration" else "RANSOMWARE-LOCKBIT3",
        "campaign": incident_id,
    }

    return {
        "incident_id": incident_id,
        "log_source": "Windows Event Log + EDR (CrowdStrike Falcon)",
        "time_range": {
            "start": base_ts.isoformat() + "Z",
            "end": ts.isoformat() + "Z",
        },
        "event_count": len(events),
        "severity_breakdown": {
            "CRITICAL": sum(1 for e in events if e["severity"] == "CRIT"),
            "HIGH": sum(1 for e in events if e["severity"] == "HIGH"),
            "WARN": sum(1 for e in events if e["severity"] == "WARN"),
        },
        "events": events,
        "ioc_summary": ioc_summary,
        "mitre_attack_coverage": [t["id"] for t in techniques],
    }


def _generate_iocs(incident_type: str) -> list:
    pool = {
        "data_exfiltration": [
            {"type": "ip", "value": "185.220.101.47", "confidence": 0.96, "source": "ThreatFox"},
            {"type": "domain", "value": "update.microsofft-cdn.com", "confidence": 0.91, "source": "OpenPhish"},
            {"type": "hash_md5", "value": hashlib.md5(b"exfil_tool").hexdigest(), "confidence": 0.88, "source": "VirusTotal"},
        ],
        "ransomware": [
            {"type": "ip", "value": "91.108.4.200", "confidence": 0.98, "source": "AbuseIPDB"},
            {"type": "hash_sha256", "value": hashlib.sha256(b"lockbit3").hexdigest(), "confidence": 0.99, "source": "MalwareBazaar"},
            {"type": "mutex", "value": "Global\\{1D2A3B4C-5E6F-7890-ABCD-EF1234567890}", "confidence": 0.95, "source": "Sandbox"},
        ],
    }
    return random.sample(pool.get(incident_type, []), k=min(2, len(pool.get(incident_type, []))))


# =============================================================================
# 4. FILE EVIDENCE — Ransomware artifacts
# =============================================================================

def generate_ransomware_artifacts(folder: Path, incident_id: str) -> dict:
    """Generate realistic ransomware file artifacts."""
    folder.mkdir(parents=True, exist_ok=True)

    # Original files (before encryption)
    originals = {
        "financial_report_Q4_2025.xlsx": b"PK\x03\x04" + b"Mock Excel financial data " * 200,
        "customer_database_export.csv": (
            b"id,name,email,credit_card,ssn\n" +
            "\n".join(
                f"{i},User {i},user{i}@corp.com,4111-1111-1111-{i:04d},{i:09d}"
                for i in range(1, 501)
            ).encode()
        ),
        "backup_credentials.txt": b"Server: db01.corp.local\nUser: sa\nPassword: P@ssw0rd2025!\n",
    }

    # XOR-encrypted versions (simulating ransomware encryption)
    xor_key = 0xDE  # simple XOR for demo
    encrypted_files = []
    original_hashes = {}
    for fname, content in originals.items():
        # Save original
        orig_path = folder / fname
        orig_path.write_bytes(content)
        original_hashes[fname] = hashlib.sha256(content).hexdigest()

        # Save encrypted version
        enc_content = bytes(b ^ xor_key for b in content)
        enc_path = folder / (fname + ".locked")
        enc_path.write_bytes(enc_content)
        encrypted_files.append({
            "original": fname,
            "encrypted": fname + ".locked",
            "original_hash_sha256": original_hashes[fname],
            "size_bytes": len(content),
        })

    # Ransom note
    ransom_note = f"""
██████╗  █████╗ ███╗   ██╗███████╗ ██████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔═══██╗████╗ ████║
██████╔╝███████║██╔██╗ ██║███████╗██║   ██║██╔████╔██║
██╔══██╗██╔══██║██║╚██╗██║╚════██║██║   ██║██║╚██╔╝██║
██║  ██║██║  ██║██║ ╚████║███████║╚██████╔╝██║ ╚═╝ ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝     ╚═╝

INCIDENT ID: {incident_id}
YOUR FILES HAVE BEEN ENCRYPTED.

All your important files have been encrypted using military-grade AES-256 encryption.
Original files have been securely deleted and cannot be recovered without our decryption key.

AFFECTED FILES: 1,247 files | 23 directories
ENCRYPTION: AES-256-CBC + RSA-4096 key wrapping

To recover your files:
  1. Do NOT attempt to modify or delete encrypted files
  2. Do NOT contact law enforcement (your files will be permanently deleted)
  3. Visit our payment portal: http://lockbit3753kfnh.onion/pay/{incident_id.lower()}
  4. Pay 4.5 BTC within 72 hours to receive your decryption key

Wallet: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
Timer: 71:58:23 remaining

[THIS IS A SIMULATED THREAT FOR SECURITY RESEARCH — ThreatLens Demo]
""".strip()

    note_path = folder / "README_RESTORE.txt"
    note_path.write_text(ransom_note, encoding="utf-8")

    # Registry modification artifact
    reg_artifact = {
        "key": "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Run",
        "value": "SystemUpdate",
        "data": "C:\\ProgramData\\WindowsUpdate\\svchost.exe -silent",
        "action": "CREATED",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "note": "Persistence mechanism — executed on every system boot"
    }
    (folder / "registry_modifications.json").write_text(json.dumps(reg_artifact, indent=2), encoding="utf-8")

    return {
        "encrypted_files": encrypted_files,
        "ransom_note": str(note_path),
        "files_affected": len(encrypted_files),
        "encryption_method": "AES-256-CBC (simulated XOR for demo)",
        "ransom_demand_btc": 4.5,
    }


# =============================================================================
# 5. THREAT TIMELINE — Attack reconstruction
# =============================================================================

def generate_threat_timeline(incident_type: str, incident_id: str, base_ts: datetime) -> dict:
    """Build a complete attack kill-chain timeline."""
    phases = {
        "data_exfiltration": [
            ("Reconnaissance",   0,    "Attacker scanned internal network (nmap -sV 192.168.10.0/24)"),
            ("Initial Access",   120,  "Phishing email opened by svc_backup — malicious macro executed"),
            ("Execution",        180,  "PowerShell reverse shell established to 185.220.101.47:4444"),
            ("Privilege Escalation", 240, "Token impersonation — SYSTEM privileges obtained"),
            ("Collection",       360,  "7z.exe compressed /data/customer_records/ (2,847 files, 2.1 GB)"),
            ("Exfiltration",     480,  "47.3 MB sent to C2 over TLS:443 in 8 chunks (DNS tunneling backup)"),
            ("Cover Tracks",     600,  "Event log cleared: Security.evtx, System.evtx, Application.evtx"),
        ],
        "ransomware": [
            ("Initial Access",       0,   "RDP brute-force successful — admin:P@ssw0rd123 on SRV-DC01"),
            ("Execution",            90,  "Ransomware binary dropped: C:\\ProgramData\\svchost.exe (4.2 MB)"),
            ("Defense Evasion",      150, "Windows Defender disabled via registry modification"),
            ("Discovery",            200, "File system enumeration — 23,847 files indexed for encryption"),
            ("Impact: Backup",       280, "Shadow copies deleted, backup services stopped"),
            ("Impact: Encryption",   340, "1,247 files encrypted with .locked extension (AES-256)"),
            ("Ransom Note",          420, "README_RESTORE.txt dropped in 23 directories"),
            ("C2 Reporting",         480, "Victim ID registered on attacker C2: secure-payments.xyz"),
        ],
    }

    timeline = []
    for phase, delta_sec, description in phases.get(incident_type, []):
        ts = base_ts + timedelta(seconds=delta_sec)
        timeline.append({
            "phase": phase,
            "timestamp": ts.isoformat() + "Z",
            "delta_seconds": delta_sec,
            "description": description,
            "confidence": round(random.uniform(0.82, 0.99), 2),
        })

    return {
        "incident_id": incident_id,
        "attack_type": incident_type,
        "kill_chain_framework": "MITRE ATT&CK v14",
        "total_attack_duration_minutes": phases.get(incident_type, [[None, 0, None]])[-1][1] // 60,
        "timeline": timeline,
        "first_seen": base_ts.isoformat() + "Z",
        "last_seen": (base_ts + timedelta(seconds=phases.get(incident_type, [[None, 480]])[-1][1])).isoformat() + "Z",
    }


# =============================================================================
# 6. MANIFEST + SHA256 CHAIN
# =============================================================================

def compute_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def build_evidence_manifest(incident: dict, folder: Path, file_inventory: list) -> dict:
    """Build a forensically valid evidence manifest with hash chain."""
    file_records = []
    for fp in sorted(folder.rglob("*")):
        if fp.is_file():
            rel = str(fp.relative_to(folder))
            size = fp.stat().st_size
            sha = compute_sha256(fp)
            file_records.append({"path": rel, "size_bytes": size, "sha256": sha})

    # Chain hash: hash of all file hashes concatenated
    chain_input = "".join(r["sha256"] for r in file_records).encode()
    chain_hash = hashlib.sha256(chain_input).hexdigest()

    total_mb = round(sum(r["size_bytes"] for r in file_records) / (1024 * 1024), 3)

    return {
        "schema_version": "2.1",
        "incident_id": incident["incident_id"],
        "capture_timestamp": datetime.utcnow().isoformat() + "Z",
        "captured_by": "ThreatLens Evidence Engine v1.0",
        "incident_metadata": {
            "severity": incident["severity"],
            "risk_score": incident["risk_score"],
            "attack_type": incident["intent"]["primary"],
            "zone": incident.get("zone", "unknown"),
            "mitre_techniques": MITRE_TECHNIQUES.get(incident["intent"]["primary"], []),
        },
        "evidence_files": file_records,
        "file_count": len(file_records),
        "total_size_mb": total_mb,
        "integrity": {
            "sha256_chain_hash": chain_hash,
            "algorithm": "SHA-256",
            "chain_method": "SHA256(concat(all_file_hashes))",
            "tamper_evident": True,
        },
        "blockchain_anchor": {
            "status": "PENDING",
            "network": "Ethereum Sepolia Testnet",
            "contract": "0x742d35Cc6634C0532925a3b8D4C9fA1234567890",
            "tx_hash": None,
            "note": "Will be anchored on Kafka manifest publish",
        },
        "ready_for_blockchain": True,
    }


# =============================================================================
# 7. MAIN ORCHESTRATION
# =============================================================================

TEST_INCIDENTS = [
    {
        "incident_id": "INC-TEST-EXFIL",
        "risk_score": 89.5,
        "severity": "HIGH",
        "intent": {"primary": "data_exfiltration", "primary_confidence": 0.87},
        "correlated_events": [
            {"source": "camera", "score": 85, "zone": "server_room",
             "timestamp": "2026-02-15T14:23:00Z"},
            {"source": "logs",   "score": 72, "zone": "server_room",
             "timestamp": "2026-02-15T14:24:00Z"},
            {"source": "network","score": 88, "zone": "server_room",
             "timestamp": "2026-02-15T14:25:00Z",
             "source_ip": "192.168.10.45", "dest_ip": "185.220.101.47"},
        ],
        "timestamp_range": {"start": "2026-02-15T14:23:00Z", "end": "2026-02-15T14:25:30Z"},
        "sources_involved": ["camera", "logs", "network"],
        "zone": "server_room",
    },
    {
        "incident_id": "INC-TEST-RANSOMWARE",
        "risk_score": 95.0,
        "severity": "CRITICAL",
        "intent": {"primary": "ransomware", "primary_confidence": 0.95},
        "correlated_events": [
            {"source": "file",   "score": 95, "zone": "internal",
             "timestamp": "2026-02-15T14:30:00Z", "ransomware_pattern": True},
            {"source": "network","score": 78, "zone": "internal",
             "timestamp": "2026-02-15T14:31:00Z"},
        ],
        "timestamp_range": {"start": "2026-02-15T14:30:00Z", "end": "2026-02-15T14:31:30Z"},
        "sources_involved": ["file", "network"],
        "zone": "internal",
    },
]


async def process_incident_enhanced(incident: dict):
    """Full enhanced evidence capture pipeline."""
    inc_id = incident["incident_id"]
    inc_type = incident["intent"]["primary"]
    base_ts = datetime.fromisoformat(
        incident["timestamp_range"]["start"].replace("Z", "+00:00")
    ).replace(tzinfo=None)

    folder = EVIDENCE_ROOT / inc_id
    folder.mkdir(parents=True, exist_ok=True)

    print(f"\n  📁 Storage: {folder}")
    sources = incident.get("sources_involved", [])
    file_inventory = []

    # --- Camera ---
    if "camera" in sources and PIL_AVAILABLE:
        print("  🎥 Generating camera evidence (annotated frames)...")
        cam_folder = folder / "camera"
        cam_folder.mkdir(exist_ok=True)
        frames = generate_video_clip_frames(cam_folder, inc_type, inc_id, base_ts, num_frames=6)
        file_inventory += [str(f) for f in cam_folder.iterdir()]
    elif "camera" in sources:
        print("  ⚠️  Camera skipped (Pillow not installed)")

    # --- Network PCAP ---
    if "network" in sources:
        print("  🌐 Generating network PCAP...")
        net_folder = folder / "network"
        net_folder.mkdir(exist_ok=True)
        pcap_data = generate_pcap(inc_type, base_ts)
        pcap_path = net_folder / "capture.pcap"
        pcap_path.write_bytes(pcap_data)
        print(f"    ✓ PCAP written ({pcap_path.stat().st_size / 1024:.1f} KB, "
              f"{len(pcap_data)} bytes)")
        file_inventory.append(str(pcap_path))

    # --- Logs ---
    if "logs" in sources or True:   # always include logs
        print("  📋 Generating structured log bundle...")
        log_folder = folder / "logs"
        log_folder.mkdir(exist_ok=True)
        log_bundle = generate_log_bundle(inc_type, inc_id, base_ts)
        log_path = log_folder / "events.json"
        log_path.write_text(json.dumps(log_bundle, indent=2), encoding="utf-8")
        # Also write raw log format
        raw_path = log_folder / "events.log"
        raw_path.write_text("\n".join(e["raw"] for e in log_bundle["events"]), encoding="utf-8")
        print(f"    ✓ {log_bundle['event_count']} events, "
              f"{log_bundle['severity_breakdown']['CRITICAL']} CRITICAL")
        file_inventory += [str(log_path), str(raw_path)]

    # --- File artifacts (ransomware) ---
    if "file" in sources or inc_type == "ransomware":
        print("  🔒 Generating ransomware file artifacts...")
        files_folder = folder / "files"
        ra = generate_ransomware_artifacts(files_folder, inc_id)
        total_size = sum(
            (files_folder / f["encrypted"]).stat().st_size
            for f in ra["encrypted_files"]
        )
        print(f"    ✓ {ra['files_affected']} file pairs encrypted, "
              f"ransom note created ({total_size/1024:.1f} KB total)")

    # --- Threat timeline ---
    print("  🗺️  Building threat timeline...")
    timeline = generate_threat_timeline(inc_type, inc_id, base_ts)
    timeline_path = folder / "threat_timeline.json"
    timeline_path.write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    print(f"    ✓ {len(timeline['timeline'])} kill-chain phases reconstructed")

    # --- Metadata ---
    metadata = {
        "incident_id": inc_id,
        "risk_score": incident["risk_score"],
        "severity": incident["severity"],
        "intent": incident["intent"]["primary"],
        "intent_confidence": incident["intent"]["primary_confidence"],
        "sources": incident.get("sources_involved", []),
        "zone": incident.get("zone"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "engine": "ThreatLens v1.0 — Evidence Capture Module",
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # --- Final manifest ---
    print("  📄 Building integrity manifest...")
    manifest = build_evidence_manifest(incident, folder, file_inventory)
    manifest_path = folder / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    total_mb = manifest["total_size_mb"]
    file_count = manifest["file_count"]
    chain_hash = manifest["integrity"]["sha256_chain_hash"]

    print(f"    ✓ {file_count} files, {total_mb} MB total")
    print(f"    ✓ SHA-256 chain: {chain_hash[:32]}...")

    return manifest


async def main():
    print("\n" + "═" * 80)
    print("  THREATLENS EVIDENCE CAPTURE — ENHANCED FORENSIC DEMO")
    print("═" * 80)
    print(f"\n  Kafka:       DISABLED (local mode)")
    print(f"  Evidence:    {EVIDENCE_ROOT.absolute()}")
    print(f"  PIL/Imaging: {'✓ AVAILABLE' if PIL_AVAILABLE else '✗ NOT INSTALLED (camera skipped)'}")
    print(f"  Incidents:   {len(TEST_INCIDENTS)}\n")

    results = []

    for incident in TEST_INCIDENTS:
        inc_id = incident["incident_id"]
        inc_type = incident["intent"]["primary"]
        sev = incident["severity"]

        print(f"\n{'─'*80}")
        print(f"  ▶ {inc_id}")
        print(f"    Type: {inc_type.upper().replace('_',' ')}  |  Severity: {sev}  "
              f"|  Risk: {incident['risk_score']}")
        print(f"{'─'*80}")

        try:
            t0 = time.time()
            manifest = await process_incident_enhanced(incident)
            elapsed = time.time() - t0
            results.append((inc_id, True, manifest, elapsed))
            print(f"\n  ✅ Complete in {elapsed:.2f}s — "
                  f"{manifest['file_count']} files, {manifest['total_size_mb']} MB")
        except Exception as e:
            import traceback
            print(f"\n  ❌ Error: {e}")
            traceback.print_exc()
            results.append((inc_id, False, str(e), 0))

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'═'*80}")
    print("  📊  DEMO SUMMARY")
    print(f"{'═'*80}\n")

    ok = sum(1 for _, s, *_ in results if s)
    print(f"  Processed: {ok}/{len(results)} incidents\n")

    for inc_id, success, data, elapsed in results:
        if success:
            m = data
            folder = EVIDENCE_ROOT / inc_id
            print(f"  ✅  {inc_id}")
            print(f"      Files:      {m['file_count']}")
            print(f"      Size:       {m['total_size_mb']} MB")
            print(f"      Integrity:  SHA-256 chain — {m['integrity']['sha256_chain_hash'][:24]}...")
            print(f"      Duration:   {elapsed:.2f}s")
            print(f"      Path:       {folder}")
            print()
        else:
            print(f"  ❌  {inc_id}: {data}\n")

    print("  📁 Evidence tree:\n")
    for incident in TEST_INCIDENTS:
        folder = EVIDENCE_ROOT / incident["incident_id"]
        if folder.exists():
            total = 0
            for fp in folder.rglob("*"):
                if fp.is_file():
                    total += fp.stat().st_size
            print(f"     {incident['incident_id']}/ ({total/1024:.1f} KB)")
            for fp in sorted(folder.rglob("*")):
                if fp.is_file():
                    rel = fp.relative_to(folder)
                    print(f"       ├─ {rel}  ({fp.stat().st_size:,} bytes)")

    print()
    if not PIL_AVAILABLE:
        print("  💡 Install Pillow for camera frames:  pip install pillow")
    print("  💡 Open evidence/ in Explorer to review all artifacts")
    print(f"\n{'═'*80}\n")


if __name__ == "__main__":
    asyncio.run(main())