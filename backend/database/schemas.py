from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Incident(Base):
    """Core incident table storing all correlated security incidents"""
    __tablename__ = "incidents"
    
    incident_id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    risk_score = Column(Integer, index=True)
    severity = Column(String, index=True)  # LOW/MEDIUM/HIGH/CRITICAL
    rule_name = Column(String)
    sources_involved = Column(JSON)       # ["camera", "logs", "network"]
    correlated_events = Column(JSON)      # full event list
    intent_primary = Column(String, index=True)
    intent_confidence = Column(Float)
    mitre_ttps = Column(JSON)             # ["T1078", "T1041"]
    current_attack_stage = Column(String)
    predicted_next_move = Column(JSON)
    nlg_explanation = Column(JSON)        # full NLG output
    sandbox_triggered = Column(Boolean, default=False)
    evidence_captured = Column(Boolean, default=False)
    blockchain_anchored = Column(Boolean, default=False)
    status = Column(String, default="open", index=True)  # open/investigating/resolved
    zone = Column(String)
    neo4j_node_ids = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Evidence(Base):
    """Evidence files with blockchain verification"""
    __tablename__ = "evidence"
    
    evidence_id = Column(String, primary_key=True)
    incident_id = Column(String, index=True)
    capture_timestamp = Column(DateTime)
    evidence_type = Column(String)    # video/logs/pcap/file/screenshot
    file_path = Column(String)        # MinIO path
    sha256_hash = Column(String, index=True)
    blockchain_tx_hash = Column(String)
    blockchain_block_number = Column(Integer)
    verified = Column(Boolean, default=False)
    evidence_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class SandboxResult(Base):
    """Malware sandbox detonation results"""
    __tablename__ = "sandbox_results"
    
    result_id = Column(String, primary_key=True)
    incident_id = Column(String, index=True)
    file_hash = Column(String, index=True)
    file_analyzed = Column(String)
    verdict = Column(String, index=True)          # MALICIOUS/SUSPICIOUS/BENIGN
    confidence_score = Column(Integer)
    behavioral_summary = Column(JSON)
    extracted_iocs = Column(JSON)
    screenshot_paths = Column(JSON)   # list of MinIO paths
    screenshot_sequence = Column(JSON)  # ordered list of screenshot files
    mitre_behaviors = Column(JSON)
    detonation_timestamp = Column(DateTime)
    detonation_duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class IOC(Base):
    """Indicators of Compromise"""
    __tablename__ = "iocs"
    
    ioc_id = Column(String, primary_key=True)
    incident_id = Column(String, index=True)
    ioc_type = Column(String, index=True)         # ip/domain/hash/registry
    value = Column(String, index=True)
    confidence = Column(Float)
    source = Column(String)           # sandbox/manual/feed
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    times_seen = Column(Integer, default=1)
    blocked = Column(Boolean, default=False)
    threat_level = Column(String)     # low/medium/high/critical
    ioc_metadata = Column(JSON)


class SystemHealth(Base):
    """System health monitoring for data sources"""
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String, index=True)  # network/camera/rf/logs/files/sandbox
    status = Column(String)           # operational/degraded/down
    last_heartbeat = Column(DateTime)
    metrics = Column(JSON)            # source-specific metrics
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertEvent(Base):
    """Raw alert events before correlation"""
    __tablename__ = "alert_events"
    
    event_id = Column(String, primary_key=True)
    source_type = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    anomaly_score = Column(Integer)
    event_data = Column(JSON)
    correlated_to_incident = Column(String, index=True)  # incident_id or null
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
