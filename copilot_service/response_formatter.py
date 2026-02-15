import re

def extract_incident_ids(text: str):
    return list(set(re.findall(r'INC-\d{4}-\d+', text)))

def format_response(question: str, raw_response: str):

    incident_ids = extract_incident_ids(raw_response)

    confidence = "high"
    if "insufficient data" in raw_response.lower():
        confidence = "low"

    return {
        "question": question,
        "response": raw_response,
        "supporting_incident_ids": incident_ids,
        "confidence": confidence
    }
