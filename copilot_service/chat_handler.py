from context_retriever import retrieve_context
from prompt_builder import build_prompt
from phi_client import query_llm
from response_formatter import format_response

def handle_chat(question: str):

    context = retrieve_context(question)

    if not context:
        return {
            "question": question,
            "response": "No relevant security events found in the last indexed data.",
            "supporting_incident_ids": [],
            "confidence": "low"
        }

    prompt = build_prompt(question, context)

    raw_output = query_llm(prompt)

    structured_output = format_response(question, raw_output)

    return structured_output
