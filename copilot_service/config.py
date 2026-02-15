import os

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "events")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi")

MAX_CONTEXT_RESULTS = 20
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 400
