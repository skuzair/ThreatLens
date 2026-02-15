"""
Evidence Manifest Builder - Fixed Version
"""

from datetime import datetime
from utils import get_folder_size


def build_manifest(incident_id, camera, logs, network, files, folder):
    """
    Build a complete evidence manifest for blockchain anchoring.
    
    Args:
        incident_id: Unique incident identifier
        camera: Camera evidence dict
        logs: Log evidence dict
        network: Network evidence dict
        files: File evidence dict
        folder: Base evidence folder path
    
    Returns:
        Dict containing complete evidence manifest
    """
    
    # Calculate total size
    size_mb = round(get_folder_size(folder) / (1024 * 1024), 2)

    manifest = {
        "incident_id": incident_id,
        "capture_timestamp": datetime.utcnow().isoformat(),
        "evidence": {
            "camera": camera or {},
            "logs": logs or {},
            "network": network or {},
            "files": files or {}
        },
        "total_size_mb": size_mb,
        "folder_path": folder,
        "ready_for_blockchain": True,
        "evidence_hash": None  # Will be computed by blockchain service
    }
    
    return manifest