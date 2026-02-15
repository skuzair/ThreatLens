"""
IOC Extractor
=============
Extracts Indicators of Compromise from the behavioral log.
"""


def extract_iocs(log: dict, file_hash: str) -> dict:
    connections = log.get("network_connections_attempted", [])

    ips     = []
    domains = []

    for c in connections:
        if c.get("ip"):     ips.append(c["ip"])
        if c.get("domain"): domains.append(c["domain"])

    # Derive MITRE behaviours from log fields
    mitre = []
    if log.get("files_encrypted", 0) > 0:        mitre.append("T1486")
    if log.get("shadow_copies_deleted"):          mitre.append("T1490")
    if connections:                               mitre.append("T1071")
    if log.get("registry_modified"):             mitre.append("T1547")
    if log.get("records_exfiltrated", 0) > 0:    mitre.append("T1041")
    if log.get("ransom_note_created"):            mitre.append("T1486")

    return {
        "ips":              list(set(ips)),
        "domains":          list(set(domains)),
        "file_hashes":      [file_hash],
        "registry_keys":    log.get("registry_modified",           []),
        "processes":        log.get("processes_spawned_suspicious", []),
        "mitre_behaviors":  list(set(mitre)),
    }