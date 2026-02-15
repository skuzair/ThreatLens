import ollama
from config import OLLAMA_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

def query_llm(prompt: str):

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise cybersecurity SOC analyst assistant. Only use provided data."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": LLM_TEMPERATURE,
            "num_predict": LLM_MAX_TOKENS,
            "top_p": 0.9
        }
    )

    return response["message"]["content"]
