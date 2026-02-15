"""
Network Evidence Capture - Fixed Version
"""

import os
from utils import ensure_dir


async def capture_network(incident, base_folder):
    """
    Capture network traffic related to the incident.
    
    For now, this creates a mock PCAP file.
    In production, you would:
    1. Query MinIO for stored packet captures
    2. Filter by timestamp range and IPs
    3. Save to evidence folder
    """
    net_folder = os.path.join(base_folder, "network")
    ensure_dir(net_folder)

    # Mock PCAP file (in production, copy actual PCAP from MinIO)
    mock_path = os.path.join(net_folder, "capture.pcap")

    with open(mock_path, "w") as f:
        f.write("Mock PCAP content - replace with actual packet capture")

    # Extract network summary from incident
    network_events = [
        e for e in incident.get("correlated_events", [])
        if e.get("source") == "network"
    ]
    
    summary = {
        "event_count": len(network_events),
        "source_ips": list(set(e.get("source_ip", "unknown") for e in network_events)),
        "dest_ips": list(set(e.get("dest_ip", "unknown") for e in network_events))
    }

    return {
        "pcap_path": mock_path,
        "packets_captured": 0,  # Update when real PCAP is implemented
        "flow_summary": summary
    }