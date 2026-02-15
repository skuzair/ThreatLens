import json

def build_prompt(question: str, context_events: list):

    context_json = json.dumps(context_events, indent=2)

    prompt = f"""
You are a cybersecurity SOC analyst assistant.

STRICT RULES:
- Use ONLY the provided security event data.
- Do NOT invent or assume missing details.
- If data is insufficient, clearly say so.
- Reference timestamps and risk scores explicitly.

SECURITY EVENT DATA:
{context_json}

ANALYST QUESTION:
{question}

Provide:
1. Clear summary
2. Timeline of events (chronological)
3. Risk assessment explanation
4. Recommended actions
"""

    return prompt
