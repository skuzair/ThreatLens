from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class EvidenceBase(BaseModel):
    evidence_id: str
    incident_id: str
    capture_timestamp: datetime
    evidence_type: str  # video/logs/pcap/file/screenshot
    file_path: str


class EvidenceCreate(EvidenceBase):
    sha256_hash: str
    metadata: Optional[Dict[str, Any]] = None


class EvidenceResponse(EvidenceBase):
    sha256_hash: str
    blockchain_tx_hash: Optional[str]
    blockchain_block_number: Optional[int]
    verified: bool
    metadata: Optional[Dict[str, Any]]
    presigned_url: Optional[str] = None  # Generated at request time
    polygonscan_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceManifest(BaseModel):
    incident_id: str
    evidence: Dict[str, Any]  # Full evidence structure from Kafka


class EvidenceVerificationRequest(BaseModel):
    file_hash: str


class EvidenceVerificationResponse(BaseModel):
    verified: bool
    hash_matches: bool
    blockchain_confirmed: bool
    blockchain_tx_hash: Optional[str]
    message: str
