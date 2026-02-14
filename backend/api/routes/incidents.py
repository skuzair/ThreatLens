from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime

from database.postgres import get_db_session
from database.schemas import Incident as IncidentDB
from models.incident import (
    IncidentResponse, IncidentListResponse, IncidentUpdate, IncidentCreate,
    TimelineEvent, AttackGraph, AttackGraphNode, AttackGraphEdge
)

router = APIRouter()


@router.post("/", response_model=IncidentResponse, status_code=201)
async def create_incident(
    incident: IncidentCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new incident
    
    - **incident_id**: Unique identifier for the incident
    - **timestamp**: When the incident occurred
    - **risk_score**: Risk score (0-100)
    - **severity**: Severity level (CRITICAL/HIGH/MEDIUM/LOW)
    - **rule_name**: Name of the triggered rule
    - **sources_involved**: List of data sources involved
    - **intent_primary**: Primary attack intent
    - **intent_confidence**: Confidence in intent classification (0.0-1.0)
    - **zone**: Network zone or area affected
    """
    try:
        # Check if incident already exists
        existing_query = select(IncidentDB).where(IncidentDB.incident_id == incident.incident_id)
        existing_result = await db.execute(existing_query)
        existing_incident = existing_result.scalar_one_or_none()
        
        if existing_incident:
            raise HTTPException(status_code=409, detail=f"Incident {incident.incident_id} already exists")
        
        # Create new incident database record
        db_incident = IncidentDB(
            incident_id=incident.incident_id,
            timestamp=incident.timestamp,
            risk_score=incident.risk_score,
            severity=incident.severity.value,
            rule_name=incident.rule_name,
            sources_involved=incident.sources_involved,
            correlated_events=incident.correlated_events,
            intent_primary=incident.intent_primary,
            intent_confidence=incident.intent_confidence,
            mitre_ttps=incident.mitre_ttps,
            current_attack_stage=incident.current_attack_stage,
            predicted_next_move=incident.predicted_next_move,
            nlg_explanation=incident.nlg_explanation,
            zone=incident.zone,
            neo4j_node_ids=incident.neo4j_node_ids,
            sandbox_triggered=False,
            evidence_captured=False,
            blockchain_anchored=False,
            status="open",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_incident)
        await db.commit()
        await db.refresh(db_incident)
        
        return IncidentResponse.from_orm(db_incident)
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating incident: {str(e)}")


@router.get("/", response_model=IncidentListResponse)
async def get_incidents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    source: Optional[str] = None,
    min_risk: Optional[int] = Query(None, ge=0, le=100),
    status: Optional[str] = "open",
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get paginated list of incidents with filters
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **severity**: Filter by severity (CRITICAL/HIGH/MEDIUM/LOW)
    - **source**: Filter by source type (camera/network/logs/rf/file)
    - **min_risk**: Minimum risk score (0-100)
    - **status**: Filter by status (open/investigating/resolved)
    """
    try:
        # Build query with filters
        query = select(IncidentDB)
        filters = []
        
        if status:
            filters.append(IncidentDB.status == status)
        if severity:
            filters.append(IncidentDB.severity == severity.upper())
        if min_risk is not None:
            filters.append(IncidentDB.risk_score >= min_risk)
        if source:
            # Filter incidents that involve the specified source
            filters.append(IncidentDB.sources_involved.contains([source]))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(IncidentDB)
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(IncidentDB.timestamp.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        incidents = result.scalars().all()
        
        return IncidentListResponse(
            incidents=[IncidentResponse.from_orm(inc) for inc in incidents],
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving incidents: {str(e)}")


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get full details of a specific incident"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        return IncidentResponse.from_orm(incident)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving incident: {str(e)}")


@router.get("/{incident_id}/timeline", response_model=List[TimelineEvent])
async def get_incident_timeline(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get ordered timeline of correlated events for an incident"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        # Extract and format correlated events
        events = incident.correlated_events or []
        timeline = []
        
        for event in events:
            timeline.append(TimelineEvent(
                event_id=event.get("event_id", ""),
                source_type=event.get("source_type", ""),
                timestamp=datetime.fromisoformat(event.get("timestamp", datetime.now().isoformat())),
                score=event.get("score", 0),
                description=event.get("description", ""),
                metadata=event.get("metadata", {})
            ))
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.timestamp)
        
        return timeline
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving timeline: {str(e)}")


@router.get("/{incident_id}/graph", response_model=AttackGraph)
async def get_attack_graph(
    incident_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get attack graph (nodes and edges) for D3.js visualization"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        # Build graph from correlated events
        events = incident.correlated_events or []
        nodes = []
        edges = []
        
        for i, event in enumerate(events):
            nodes.append(AttackGraphNode(
                id=event.get("event_id", f"event-{i}"),
                source_type=event.get("source_type", "unknown"),
                score=event.get("score", 0),
                label=event.get("description", "")[:30],
                timestamp=datetime.fromisoformat(event.get("timestamp", datetime.now().isoformat()))
            ))
            
            # Create edges between sequential events
            if i > 0:
                edges.append(AttackGraphEdge(
                    source=events[i-1].get("event_id", f"event-{i-1}"),
                    target=event.get("event_id", f"event-{i}"),
                    confidence=0.85,
                    relationship="leads_to"
                ))
        
        return AttackGraph(nodes=nodes, edges=edges)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving attack graph: {str(e)}")


@router.patch("/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    update: IncidentUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update incident status and flags"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
        
        # Update fields
        if update.status is not None:
            incident.status = update.status.value
        if update.sandbox_triggered is not None:
            incident.sandbox_triggered = update.sandbox_triggered
        if update.evidence_captured is not None:
            incident.evidence_captured = update.evidence_captured
        if update.blockchain_anchored is not None:
            incident.blockchain_anchored = update.blockchain_anchored
        
        incident.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(incident)
        
        return {"message": "Incident updated successfully", "incident_id": incident_id}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating incident: {str(e)}")


@router.get("/stats/summary")
async def get_incident_summary(
    db: AsyncSession = Depends(get_db_session)
):
    """Get incident statistics summary"""
    try:
        # Count by severity
        severity_query = select(
            IncidentDB.severity,
            func.count(IncidentDB.incident_id).label('count')
        ).where(IncidentDB.status == 'open').group_by(IncidentDB.severity)
        
        severity_result = await db.execute(severity_query)
        severity_counts = {row[0]: row[1] for row in severity_result.all()}
        
        # Count by status
        status_query = select(
            IncidentDB.status,
            func.count(IncidentDB.incident_id).label('count')
        ).group_by(IncidentDB.status)
        
        status_result = await db.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}
        
        return {
            "by_severity": severity_counts,
            "by_status": status_counts,
            "total_open": sum(severity_counts.values())
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")
