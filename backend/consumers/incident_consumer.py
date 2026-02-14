from consumers.base_consumer import BaseConsumer
from api.websockets.manager import websocket_manager
from database.postgres import AsyncSessionLocal
from database.schemas import Incident, Evidence, SandboxResult, IOC
import json
from datetime import datetime


class IncidentConsumer(BaseConsumer):
    """Consumes incident-related Kafka topics and updates database + WebSocket clients"""
    
    def __init__(self):
        super().__init__(
            topics=[
                "correlated-incidents",
                "evidence-manifest",
                "sandbox-results",
                "nlg-explanations",
                "blockchain-receipts"
            ],
            group_id="incident-processor"
        )
    
    async def handle_message(self, topic: str, data: dict):
        """Route messages to appropriate handler based on topic"""
        try:
            if topic == "correlated-incidents":
                await self.handle_incident(data)
            elif topic == "evidence-manifest":
                await self.handle_evidence(data)
            elif topic == "sandbox-results":
                await self.handle_sandbox(data)
            elif topic == "nlg-explanations":
                await self.handle_explanation(data)
            elif topic == "blockchain-receipts":
                await self.handle_blockchain(data)
        except Exception as e:
            print(f"❌ Error in IncidentConsumer.handle_message for {topic}: {e}")
    
    async def handle_incident(self, incident_data: dict):
        """Process new correlated incident"""
        try:
            # Save to PostgreSQL
            async with AsyncSessionLocal() as db:
                incident = Incident(
                    incident_id=incident_data["incident_id"],
                    timestamp=datetime.fromisoformat(incident_data["timestamp"]),
                    risk_score=incident_data["risk_score"],
                    severity=incident_data["severity"],
                    rule_name=incident_data["rule_name"],
                    sources_involved=incident_data["sources_involved"],
                    correlated_events=incident_data.get("correlated_events", []),
                    intent_primary=incident_data["intent"]["primary"],
                    intent_confidence=incident_data["intent"]["confidence"],
                    mitre_ttps=incident_data.get("mitre_ttps", []),
                    current_attack_stage=incident_data.get("current_attack_stage"),
                    predicted_next_move=incident_data.get("predicted_next_move"),
                    nlg_explanation=incident_data.get("nlg_explanation"),
                    zone=incident_data.get("zone", "unknown"),
                    neo4j_node_ids=incident_data.get("neo4j_node_ids", [])
                )
                db.add(incident)
                await db.commit()
            
            # Broadcast to all connected WebSocket clients
            await websocket_manager.broadcast_to_alerts({
                "type": "new_incident",
                "data": incident_data
            })
            
            print(f"✅ New incident: {incident_data['incident_id']} | Risk: {incident_data['risk_score']}")
            
        except Exception as e:
            print(f"❌ Error handling incident: {e}")
    
    async def handle_evidence(self, evidence_data: dict):
        """Process evidence manifest"""
        try:
            incident_id = evidence_data["incident_id"]
            
            # Save evidence records to PostgreSQL
            async with AsyncSessionLocal() as db:
                for evidence_type, evidence_info in evidence_data.get("evidence", {}).items():
                    evidence = Evidence(
                        evidence_id=f"{incident_id}-{evidence_type}-{int(datetime.now().timestamp())}",
                        incident_id=incident_id,
                        capture_timestamp=datetime.fromisoformat(evidence_info["timestamp"]),
                        evidence_type=evidence_type,
                        file_path=evidence_info.get("file_path", ""),
                        sha256_hash=evidence_info.get("sha256", ""),
                        metadata=evidence_info
                    )
                    db.add(evidence)
                
                # Update incident record
                result = await db.execute(
                    f"UPDATE incidents SET evidence_captured=true WHERE incident_id='{incident_id}'"
                )
                await db.commit()
            
            print(f"✅ Evidence captured for incident: {incident_id}")
            
        except Exception as e:
            print(f"❌ Error handling evidence: {e}")
    
    async def handle_sandbox(self, sandbox_data: dict):
        """Process sandbox detonation results"""
        try:
            # Save sandbox result to PostgreSQL
            async with AsyncSessionLocal() as db:
                result = SandboxResult(
                    result_id=sandbox_data["result_id"],
                    incident_id=sandbox_data["incident_id"],
                    file_hash=sandbox_data["file_hash"],
                    file_analyzed=sandbox_data.get("file_analyzed", ""),
                    verdict=sandbox_data["verdict"],
                    confidence_score=sandbox_data["confidence_score"],
                    behavioral_summary=sandbox_data.get("behavioral_summary", {}),
                    extracted_iocs=sandbox_data.get("extracted_iocs", {}),
                    screenshot_paths=sandbox_data.get("screenshot_paths", []),
                    screenshot_sequence=sandbox_data.get("screenshot_sequence", []),
                    mitre_behaviors=sandbox_data.get("mitre_behaviors", []),
                    detonation_timestamp=datetime.fromisoformat(sandbox_data["detonation_timestamp"]),
                    detonation_duration_seconds=sandbox_data.get("detonation_duration_seconds", 0)
                )
                db.add(result)
                
                # Extract and save IOCs
                for ioc_type, ioc_values in sandbox_data.get("extracted_iocs", {}).items():
                    if ioc_type == "mitre_behaviors":
                        continue
                    
                    values = ioc_values if isinstance(ioc_values, list) else [ioc_values]
                    for value in values:
                        ioc = IOC(
                            ioc_id=f"{sandbox_data['incident_id']}-{ioc_type}-{value}",
                            incident_id=sandbox_data["incident_id"],
                            ioc_type=ioc_type,
                            value=value,
                            confidence=0.9,
                            source="sandbox",
                            threat_level="high" if sandbox_data["verdict"] == "MALICIOUS" else "medium"
                        )
                        db.add(ioc)
                
                await db.commit()
            
            # Notify dashboard
            await websocket_manager.broadcast_to_alerts({
                "type": "sandbox_complete",
                "data": sandbox_data
            })
            
            print(f"✅ Sandbox analysis complete: {sandbox_data['verdict']} | {sandbox_data['file_analyzed']}")
            
        except Exception as e:
            print(f"❌ Error handling sandbox result: {e}")
    
    async def handle_explanation(self, explanation_data: dict):
        """Process NLG explanation update"""
        try:
            incident_id = explanation_data["incident_id"]
            
            # Update incident with explanation
            async with AsyncSessionLocal() as db:
                await db.execute(
                    f"UPDATE incidents SET nlg_explanation='{json.dumps(explanation_data['explanation'])}' WHERE incident_id='{incident_id}'"
                )
                await db.commit()
            
            print(f"✅ NLG explanation updated for incident: {incident_id}")
            
        except Exception as e:
            print(f"❌ Error handling explanation: {e}")
    
    async def handle_blockchain(self, blockchain_data: dict):
        """Process blockchain anchoring receipts"""
        try:
            incident_id = blockchain_data["incident_id"]
            
            # Update evidence records with blockchain info
            async with AsyncSessionLocal() as db:
                for receipt in blockchain_data.get("receipts", []):
                    await db.execute(
                        f"""UPDATE evidence 
                        SET blockchain_tx_hash='{receipt['tx_hash']}',
                            blockchain_block_number={receipt['block_number']},
                            verified=true
                        WHERE sha256_hash='{receipt['sha256']}'"""
                    )
                
                # Update incident
                await db.execute(
                    f"UPDATE incidents SET blockchain_anchored=true WHERE incident_id='{incident_id}'"
                )
                await db.commit()
            
            print(f"✅ Blockchain anchoring complete for incident: {incident_id}")
            
        except Exception as e:
            print(f"❌ Error handling blockchain receipt: {e}")
