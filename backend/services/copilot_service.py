import httpx
import json
from typing import Dict, List
from config import settings


class CopilotService:
    """Service for SOC Copilot using Ollama LLM"""
    
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_HOST}/api/chat"
        self.model = settings.OLLAMA_MODEL
    
    async def query(self, question: str, context_events: List[Dict] = None) -> Dict:
        """
        Query the LLM copilot with security context
        
        Args:
            question: User's question
            context_events: Relevant security events for context
        
        Returns:
            Response with answer and supporting evidence
        """
        try:
            # Build prompt with context
            prompt = self._build_prompt(question, context_events or [])
            
            # Send to Ollama
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "options": {
                            "temperature": 0.1,  # Low temperature for factual responses
                            "top_p": 0.9
                        },
                        "stream": False
                    }
                )
            
            if response.status_code != 200:
                return {
                    "question": question,
                    "response": "Sorry, the copilot service is currently unavailable.",
                    "supporting_events": [],
                    "context_event_count": 0
                }
            
            result = response.json()
            llm_response = result["message"]["content"]
            
            return {
                "question": question,
                "response": llm_response,
                "supporting_events": [e.get("event_id", "") for e in (context_events or [])[:5]],
                "context_event_count": len(context_events or [])
            }
        
        except httpx.TimeoutException:
            return {
                "question": question,
                "response": "The request timed out. Please try a simpler question.",
                "supporting_events": [],
                "context_event_count": 0
            }
        except Exception as e:
            print(f"❌ Error in copilot query: {e}")
            return {
                "question": question,
                "response": f"An error occurred: {str(e)}",
                "supporting_events": [],
                "context_event_count": 0
            }
    
    def _build_prompt(self, question: str, context: List[Dict]) -> str:
        """Build structured prompt for the LLM"""
        context_str = json.dumps(context[:10], indent=2) if context else "No context available"
        
        return f"""You are a cybersecurity SOC analyst assistant for ThreatLens AI.
Answer using ONLY the security event data provided below.
Do not invent information. Be concise and reference specific timestamps, incident IDs, and risk scores.
If you don't have enough information to answer, say so.

SECURITY EVENT DATA:
{context_str}

ANALYST QUESTION: {question}

Provide a clear, professional answer suitable for a SOC analyst. Reference specific incident IDs when relevant.
Format your response in a structured way using bullet points when listing multiple items."""


# Global instance
copilot_service = CopilotService()
