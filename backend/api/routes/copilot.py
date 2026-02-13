from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.copilot_service import copilot_service
from database.postgres import get_db_session
from database.schemas import Incident as IncidentDB
from models.alert import CopilotQuery, CopilotResponse
from sqlalchemy import select

router = APIRouter()


@router.post("/query", response_model=CopilotResponse)
async def copilot_query(
    query: CopilotQuery,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Query the SOC Copilot with natural language questions
    
    The copilot will retrieve relevant security context and provide answers
    using the Mistral-7B LLM running locally via Ollama.
    """
    # Retrieve relevant context from database
    # For now, get recent high-severity incidents
    context_query = select(IncidentDB).where(
        IncidentDB.risk_score >= 70
    ).order_by(IncidentDB.timestamp.desc()).limit(10)
    
    result = await db.execute(context_query)
    incidents = result.scalars().all()
    
    # Build context
    context_events = []
    for incident in incidents:
        context_events.append({
            "event_id": incident.incident_id,
            "incident_id": incident.incident_id,
            "timestamp": incident.timestamp.isoformat(),
            "severity": incident.severity,
            "risk_score": incident.risk_score,
            "rule_name": incident.rule_name,
            "sources": incident.sources_involved,
            "intent": incident.intent_primary,
            "zone": incident.zone,
            "status": incident.status
        })
    
    # Query copilot
    response = await copilot_service.query(query.question, context_events)
    
    # Add incident references
    incident_refs = [e["incident_id"] for e in context_events[:5]]
    response["incident_references"] = incident_refs
    
    return CopilotResponse(**response)
