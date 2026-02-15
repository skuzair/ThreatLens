"""
Evidence Orchestrator - Fixed Version

Coordinates evidence capture from all sources when an incident is detected.
"""

import os
from datetime import datetime
from camera_capture import capture_camera
from log_capture import capture_logs
from network_capture import capture_network
from file_capture import capture_files
from manifest_builder import build_manifest
from metadata_builder import create_metadata
from kafka_producer import publish_manifest
from config import EVIDENCE_ROOT


async def process_incident(incident):
    """
    Main orchestration function for evidence capture.
    
    Args:
        incident: Dict containing incident details from correlation engine
    """
    
    incident_id = incident["incident_id"]
    base_folder = os.path.join(EVIDENCE_ROOT, incident_id)
    os.makedirs(base_folder, exist_ok=True)

    print(f"[Evidence] Creating evidence package for {incident_id}")
    print(f"[Evidence] Storage location: {base_folder}")

    # Capture from all sources
    camera_evidence = {}
    logs_evidence = {}
    network_evidence = {}
    files_evidence = {}
    
    sources = incident.get("sources_involved", [])
    
    if "camera" in sources:
        print("[Evidence] Capturing camera footage...")
        camera_evidence = await capture_camera(incident, base_folder)
    
    if "logs" in sources:
        print("[Evidence] Capturing log snippets...")
        logs_evidence = await capture_logs(incident, base_folder)
    
    if "network" in sources:
        print("[Evidence] Capturing network traffic...")
        network_evidence = await capture_network(incident, base_folder)
    
    if "file" in sources:
        print("[Evidence] Capturing file artifacts...")
        files_evidence = await capture_files(incident, base_folder)
    
    # Create metadata
    print("[Evidence] Building metadata...")
    metadata = create_metadata(incident, base_folder)
    
    # Build manifest
    print("[Evidence] Building evidence manifest...")
    manifest = build_manifest(
        incident_id,
        camera_evidence,
        logs_evidence,
        network_evidence,
        files_evidence,
        base_folder
    )
    
    # Publish to Kafka
    print("[Evidence] Publishing manifest to Kafka...")
    publish_manifest(manifest)
    
    print(f"[Evidence] ✅ Evidence capture complete for {incident_id}")
    print(f"[Evidence] Total size: {manifest.get('total_size_mb', 0)} MB")
    
    return manifest