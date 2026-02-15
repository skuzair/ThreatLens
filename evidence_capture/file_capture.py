"""
File Evidence Capture - Fixed Version
"""

import os
import shutil
from utils import ensure_dir, compute_sha256


async def capture_files(incident, base_folder):
    """
    Capture suspicious files mentioned in the incident.
    """
    file_folder = os.path.join(base_folder, "files")
    ensure_dir(file_folder)

    # Get suspicious file path from incident events
    suspicious = None
    for event in incident.get("correlated_events", []):
        if event.get("source") == "file" and "file_path" in event:
            suspicious = event["file_path"]
            break
    
    if not suspicious:
        print("[Evidence] No suspicious file path in incident")
        return {"note": "No suspicious file identified"}

    if not os.path.exists(suspicious):
        print(f"[Evidence] File not found: {suspicious}")
        return {"note": f"File not found: {suspicious}"}

    # Copy file to evidence folder
    dest = os.path.join(file_folder, os.path.basename(suspicious))
    shutil.copy(suspicious, dest)

    # Compute hash
    hash_value = compute_sha256(dest)

    return {
        "suspicious_file": dest,
        "sha256": hash_value,
        "original_path": suspicious,
        "file_size_bytes": os.path.getsize(dest)
    }