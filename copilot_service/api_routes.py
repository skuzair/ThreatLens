from fastapi import FastAPI
from pydantic import BaseModel
from chat_handler import handle_chat

app = FastAPI()

class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    return handle_chat(request.question)
