"""
Sandbox Screenshot Engine
=========================
Generates realistic PIL frames that look like a sandbox VM console
showing malware execution in real time. Each frame shows accumulating
terminal output + live metrics panel on the right.
"""

from pathlib import Path
from datetime import datetime, timedelta
import random

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ── Palette ────────────────────────────────────────────────────────────────
BG          = (10,  12,  18)      # near-black
PANEL_BG    = (16,  20,  30)      # slightly lighter for right panel
BORDER      = (40,  60,  90)      # dim blue border
GREEN       = (0,   230, 80)      # terminal green
RED         = (220, 50,  50)      # alert red
ORANGE      = (255, 140, 0)       # warning orange
YELLOW      = (240, 200, 40)      # highlight
WHITE       = (220, 225, 235)     # normal text
DIM         = (80,  90,  110)     # dim text
CYAN        = (0,   200, 220)     # phase headers
MAGENTA     = (200, 60,  180)     # IOC/hash highlights


def _colour_for_line(line: str):
    l = line.lower()
    if l.startswith("[phase"):              return CYAN
    if l.startswith("[+]"):                return GREEN
    if l.startswith("[*]"):                return WHITE
    if l.startswith("[!]") or "error" in l: return RED
    if "encrypt" in l or "locked" in l:    return ORANGE
    if "exfil" in l or "dns" in l:         return MAGENTA
    if "beacon" in l or "c2" in l:         return YELLOW
    return DIM


def _bar(draw, x, y, w, h, pct, color, bg=(30, 35, 50)):
    draw.rectangle([x, y, x + w, y + h], fill=bg)
    filled = int(w * min(pct, 1.0))
    if filled > 0:
        draw.rectangle([x, y, x + filled, y + h], fill=color)
    draw.rectangle([x, y, x + w, y + h], outline=BORDER, width=1)


def generate_frame(
    frame_idx: int,
    total_frames: int,
    all_lines: list,
    incident_id: str,
    attack_type: str,
    base_ts: datetime,
    out_path: Path,
    metrics: dict,
):
    """
    Render one 1280×720 sandbox console frame.

    all_lines  : complete list of terminal output lines
    frame_idx  : which frame we're on (0-based)
    metrics    : dict updated per frame (encrypted, exfil_kb, c2_hits, …)
    """
    if not PIL_AVAILABLE:
        out_path.write_bytes(b"PIL_NOT_AVAILABLE")
        return

    W, H = 1280, 720
    TERM_W = 860          # terminal takes left 860px
    PANEL_X = TERM_W + 2  # right panel starts here

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    ts = base_ts + timedelta(seconds=frame_idx * 2)

    # ── Top bar ──────────────────────────────────────────────────────────
    draw.rectangle([0, 0, W, 32], fill=(8, 10, 16))
    draw.rectangle([0, 32, W, 33], fill=BORDER)

    sandbox_label = f"  ◉ THREATLENS SANDBOX  │  {incident_id}  │  {attack_type.upper().replace('_',' ')}"
    draw.text((8, 8), sandbox_label, fill=GREEN)

    timer_sec = frame_idx * 2
    timer_str = f"{timer_sec // 60:02d}:{timer_sec % 60:02d}  {ts.strftime('%H:%M:%S UTC')}  "
    draw.text((W - len(timer_str) * 7 - 4, 8), timer_str, fill=DIM)

    # ── Vertical divider ──────────────────────────────────────────────────
    draw.rectangle([TERM_W, 33, TERM_W + 1, H], fill=BORDER)

    # ── Terminal area ─────────────────────────────────────────────────────
    LINE_H   = 15
    MAX_ROWS = (H - 60) // LINE_H        # rows that fit
    progress = (frame_idx + 1) / total_frames
    lines_to_show = all_lines[:int(len(all_lines) * progress)]
    visible = lines_to_show[-MAX_ROWS:]  # scroll — show latest

    for row, line in enumerate(visible):
        y = 40 + row * LINE_H
        colour = _colour_for_line(line)
        # Truncate to terminal width
        max_chars = (TERM_W - 16) // 7
        draw.text((10, y), line[:max_chars], fill=colour)

    # Blinking cursor on last line
    if frame_idx % 2 == 0 and visible:
        cy = 40 + len(visible) * LINE_H
        draw.rectangle([10, cy + 2, 16, cy + 13], fill=GREEN)

    # ── Right panel ───────────────────────────────────────────────────────
    px = PANEL_X + 8
    py = 40

    def panel_header(text, y):
        draw.rectangle([PANEL_X + 4, y, W - 4, y + 18], fill=(20, 28, 45))
        draw.text((px, y + 2), text, fill=CYAN)
        return y + 22

    def panel_row(label, value, y, vc=WHITE):
        draw.text((px,      y), label, fill=DIM)
        draw.text((px + 130, y), str(value), fill=vc)
        return y + 16

    # Status block
    py = panel_header("◈ DETONATION STATUS", py)
    phase_pct = progress
    status_color = RED if phase_pct > 0.6 else ORANGE if phase_pct > 0.3 else YELLOW
    py = panel_row("Status",    "ACTIVE" if frame_idx < total_frames - 1 else "COMPLETE",  py, status_color)
    py = panel_row("Progress",  f"{phase_pct:.0%}", py, WHITE)
    py = panel_row("Runtime",   f"{timer_sec}s / {total_frames*2}s", py)
    py = panel_row("Container", "threatlens-sandbox", py)
    py = panel_row("Image",     "python:3.11-slim",   py)
    py += 6

    # Progress bar
    _bar(draw, px, py, W - px - 8, 10, phase_pct, status_color)
    py += 18

    # Threat metrics
    py = panel_header("◈ THREAT METRICS", py)
    enc = metrics.get("files_encrypted", 0)
    enc_prog = int(enc * progress)
    py = panel_row("Files encrypted",   f"{enc_prog:,}", py, RED if enc_prog > 0 else DIM)
    if enc > 0:
        _bar(draw, px, py, W - px - 8, 8, enc_prog / max(enc, 1), RED)
        py += 14

    exfil = metrics.get("exfil_kb", 0)
    exfil_prog = round(exfil * progress, 1)
    py = panel_row("Exfil (KB)",  f"{exfil_prog}", py, MAGENTA if exfil_prog > 0 else DIM)

    c2 = metrics.get("c2_hits", 0)
    c2_prog = int(c2 * progress)
    py = panel_row("C2 beacons",  f"{c2_prog}", py, YELLOW if c2_prog > 0 else DIM)

    py = panel_row("Shadow copies",
                   "DELETED" if progress > 0.45 else "intact",
                   py,
                   RED if progress > 0.45 else GREEN)
    py = panel_row("Ransom note",
                   "DROPPED" if progress > 0.85 and enc > 0 else "pending",
                   py,
                   RED if progress > 0.85 and enc > 0 else DIM)
    py += 6

    # IOC panel
    py = panel_header("◈ INDICATORS OF COMPROMISE", py)
    iocs = metrics.get("iocs", [])
    for ioc in iocs[:6]:
        short = ioc[:30] + "…" if len(ioc) > 30 else ioc
        draw.text((px, py), f"• {short}", fill=MAGENTA)
        py += 14
    py += 4

    # MITRE ATT&CK
    py = panel_header("◈ MITRE ATT&CK", py)
    techniques = metrics.get("mitre", [])
    for tactic, tid in techniques[:5]:
        draw.text((px,       py), tid,    fill=ORANGE)
        draw.text((px + 60,  py), tactic, fill=DIM)
        py += 14

    # ── Bottom bar ────────────────────────────────────────────────────────
    draw.rectangle([0, H - 24, W, H], fill=(8, 10, 16))
    draw.rectangle([0, H - 25, W, H - 24], fill=BORDER)
    draw.text((8, H - 18), f"Frame {frame_idx+1:03d}/{total_frames:03d}", fill=DIM)
    verdict_color = RED if metrics.get("verdict") == "MALICIOUS" else ORANGE
    draw.text((TERM_W // 2 - 40, H - 18),
              f"VERDICT: {metrics.get('verdict','ANALYSING...')}",
              fill=verdict_color if metrics.get("verdict") else DIM)
    draw.text((W - 220, H - 18),
              f"Confidence: {metrics.get('confidence', '—')}",
              fill=WHITE)

    img.save(out_path, "JPEG", quality=88)