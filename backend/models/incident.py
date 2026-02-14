from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class IncidentBase(BaseModel):
    incident_id: str
    timestamp: datetime
    risk_score: int = Field(..., ge=0, le=100)
    severity: SeverityLevel
    rule_name: str
    sources_involved: List[str]
    intent_primary: str
    intent_confidence: float = Field(..., ge=0.0, le=1.0)
    zone: str


class IncidentCreate(IncidentBase):
    correlated_events: List[Dict[str, Any]]
    mitre_ttps: List[str]
    current_attack_stage: Optional[str] = None
    predicted_next_move: Optional[Dict[str, Any]] = None
    nlg_explanation: Optional[Dict[str, Any]] = None
    neo4j_node_ids: Optional[List[str]] = None


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    sandbox_triggered: Optional[bool] = None
    evidence_captured: Optional[bool] = None
    blockchain_anchored: Optional[bool] = None


class IncidentResponse(IncidentBase):
    correlated_events: List[Dict[str, Any]]
    mitre_ttps: List[str]
    current_attack_stage: Optional[str]
    predicted_next_move: Optional[Dict[str, Any]]
    nlg_explanation: Optional[Dict[str, Any]]
    sandbox_triggered: bool
    evidence_captured: bool
    blockchain_anchored: bool
    status: str
    neo4j_node_ids: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int
    page: int
    limit: int
    pages: int


class TimelineEvent(BaseModel):
    event_id: str
    source_type: str
    timestamp: datetime
    score: int
    description: str
    metadata: Dict[str, Any]


class AttackGraphNode(BaseModel):
    id: str
    source_type: str
    score: int
    label: str
    timestamp: datetime


class AttackGraphEdge(BaseModel):
    source: str
    target: str
    confidence: float
    relationship: str


class AttackGraph(BaseModel):
    nodes: List[AttackGraphNode]
    edges: List[AttackGraphEdge]
