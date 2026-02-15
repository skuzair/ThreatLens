"""
Docker Sandbox Orchestrator
============================
Runs generated attack scripts inside a real Docker container,
captures stdout/stderr, parses the structured result JSON,
and returns a full behavioral log.

Falls back to pure simulation if Docker is unavailable.
"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from attack_scripts import get_script

DOCKER_IMAGE   = "python:3.11-slim"
TIMEOUT_SEC    = 60          # max container runtime
DOCKER_MEMORY  = "256m"      # cap container RAM
DOCKER_CPUS    = "0.5"       # cap CPU


# ── helpers ────────────────────────────────────────────────────────────────

def _docker_available() -> bool:
    try:
        r = subprocess.run(
            ["docker", "info"],
            capture_output=True, timeout=5
        )
        return r.returncode == 0
    except Exception:
        return False


def _pull_image_if_needed():
    """Pull image silently; skip if already present."""
    result = subprocess.run(
        ["docker", "image", "inspect", DOCKER_IMAGE],
        capture_output=True
    )
    if result.returncode != 0:
        print(f"  [Docker] Pulling {DOCKER_IMAGE} (first run)…")
        subprocess.run(["docker", "pull", DOCKER_IMAGE], check=True)


def _parse_result_json(stdout: str) -> dict:
    """Extract the SANDBOX_RESULT_JSON line from stdout."""
    for line in stdout.splitlines():
        if line.startswith("SANDBOX_RESULT_JSON:"):
            try:
                return json.loads(line[len("SANDBOX_RESULT_JSON:"):])
            except json.JSONDecodeError:
                pass
    return {}


def _clean_stdout(stdout: str) -> list[str]:
    """Return all lines except the JSON result sentinel."""
    return [
        l for l in stdout.splitlines()
        if not l.startswith("SANDBOX_RESULT_JSON:")
    ]


# ── main entry ─────────────────────────────────────────────────────────────

def run_sandbox(incident_id: str, attack_type: str) -> dict:
    """
    Execute the attack script for *attack_type* inside Docker.

    Returns
    -------
    dict with keys:
        output_lines     – list of terminal output strings
        behavioral_log   – parsed result dict from the script
        docker_used      – bool
        exit_code        – container exit code
        duration_sec     – wall-clock runtime
    """
    script_src = get_script(attack_type)

    if _docker_available():
        return _run_in_docker(incident_id, attack_type, script_src)
    else:
        print("  [Docker] ⚠ Docker not available — running simulation fallback")
        return _run_simulation_fallback(attack_type, script_src)


def _run_in_docker(incident_id: str, attack_type: str, script_src: str) -> dict:
    """Write script to a temp file and execute inside an isolated container."""

    _pull_image_if_needed()

    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "payload.py"
        script_path.write_text(script_src, encoding="utf-8")

        cmd = [
            "docker", "run",
            "--rm",                                    # auto-remove when done
            "--network", "none",                       # NO network access
            "--memory", DOCKER_MEMORY,
            "--cpus",   DOCKER_CPUS,
            "--read-only",                             # read-only rootfs
            "--tmpfs",  "/sandbox:size=64m",           # writable tmp sandbox dir
            "--tmpfs",  "/tmp:size=16m",
            "-v", f"{script_path}:/payload.py:ro",    # inject script
            "--name", f"tl-sandbox-{incident_id.lower()}-{int(time.time())}",
            DOCKER_IMAGE,
            "python", "/payload.py"
        ]

        print(f"  [Docker] Launching container for {incident_id}…")
        t0 = time.time()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC
            )
            duration = round(time.time() - t0, 2)
            stdout   = proc.stdout
            stderr   = proc.stderr

            if proc.returncode not in (0, 1):
                # Non-zero but not a script error — Docker issue
                print(f"  [Docker] Container exit code {proc.returncode}")
                if stderr:
                    print(f"  [Docker] stderr: {stderr[:300]}")

        except subprocess.TimeoutExpired:
            duration = TIMEOUT_SEC
            stdout   = "[!] Container timed out\n"
            stderr   = ""
            print(f"  [Docker] ⚠ Container timed out after {TIMEOUT_SEC}s")

        behavioral_log = _parse_result_json(stdout)
        output_lines   = _clean_stdout(stdout)
        if stderr.strip():
            output_lines += ["", "[!] STDERR:", *stderr.strip().splitlines()]

        print(f"  [Docker] ✓ Complete in {duration}s — "
              f"{len(output_lines)} output lines")

        return {
            "output_lines":   output_lines,
            "behavioral_log": behavioral_log,
            "docker_used":    True,
            "exit_code":      proc.returncode,
            "duration_sec":   duration,
        }


def _run_simulation_fallback(attack_type: str, script_src: str) -> dict:
    """
    Execute the script in a subprocess (no Docker).
    Safe because the scripts only use stdlib and write to /sandbox/ which
    won't exist — they'll fail gracefully or write to temp dirs.
    """
    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "payload.py"
        script_path.write_text(script_src, encoding="utf-8")

        t0 = time.time()
        proc = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
            cwd=tmp,
        )
        duration = round(time.time() - t0, 2)

        behavioral_log = _parse_result_json(proc.stdout)
        output_lines   = _clean_stdout(proc.stdout)

        return {
            "output_lines":   output_lines,
            "behavioral_log": behavioral_log,
            "docker_used":    False,
            "exit_code":      proc.returncode,
            "duration_sec":   duration,
        }