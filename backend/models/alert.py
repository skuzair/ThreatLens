from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class CopilotQuery(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    question: str
    response: str
    supporting_events: List[str]
    context_event_count: int
    incident_references: Optional[List[str]] = []


class LiveMetrics(BaseModel):
    source: str  # network/camera/rf/logs/files
    timestamp: str
    metrics: Dict[str, Any]


class SystemHealthStatus(BaseModel):
    source_name: str
    status: str  # operational/degraded/down
    last_heartbeat: str
    metrics: Optional[Dict[str, Any]] = None
