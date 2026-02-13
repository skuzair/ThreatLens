from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SandboxVerdict(str, Enum):
    MALICIOUS = "MALICIOUS"
    SUSPICIOUS = "SUSPICIOUS"
    BENIGN = "BENIGN"


class SandboxResultBase(BaseModel):
    result_id: str
    incident_id: str
    file_hash: str
    file_analyzed: str
    verdict: SandboxVerdict
    confidence_score: int = Field(..., ge=0, le=100)


class SandboxResultCreate(SandboxResultBase):
    behavioral_summary: Dict[str, Any]
    extracted_iocs: Dict[str, Any]
    screenshot_paths: List[str]
    screenshot_sequence: List[str]
    mitre_behaviors: List[str]
    detonation_timestamp: datetime
    detonation_duration_seconds: int


class SandboxResultResponse(SandboxResultBase):
    behavioral_summary: Dict[str, Any]
    extracted_iocs: Dict[str, Any]
    screenshot_paths: List[str]
    screenshot_sequence: List[str]
    mitre_behaviors: List[str]
    detonation_timestamp: datetime
    detonation_duration_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True


class SandboxScreenshotRequest(BaseModel):
    screenshot_path: str


class IOCExtract(BaseModel):
    ips: Optional[List[str]] = []
    domains: Optional[List[str]] = []
    hashes: Optional[List[str]] = []
    registry_keys: Optional[List[str]] = []
    file_paths: Optional[List[str]] = []
