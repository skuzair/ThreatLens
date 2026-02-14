from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class IOCBase(BaseModel):
    ioc_id: str
    ioc_type: str  # ip/domain/hash/registry
    value: str
    confidence: float
    source: str  # sandbox/manual/feed


class IOCCreate(IOCBase):
    incident_id: Optional[str] = None
    threat_level: Optional[str] = "medium"
    metadata: Optional[Dict[str, Any]] = None


class IOCUpdate(BaseModel):
    blocked: Optional[bool] = None
    threat_level: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IOCResponse(IOCBase):
    incident_id: Optional[str]
    first_seen: datetime
    last_seen: datetime
    times_seen: int
    blocked: bool
    threat_level: str
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class IOCListResponse(BaseModel):
    iocs: list[IOCResponse]
    total: int
    page: int
    limit: int
