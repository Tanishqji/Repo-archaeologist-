from typing import List, Optional
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.api.analyze import rate_limiter, vector_store
from app.chat.rag import ChatMessage, RepoChatService
from app.core.errors import AppError, ErrorCode

router = APIRouter()
chat_service = RepoChatService(store=vector_store)

class ChatRequest(BaseModel):
    owner: str
    repo: str
    sha: Optional[str] = "latest"
    question: str
    history: List[ChatMessage] = Field(default_factory=list)

@router.post("/chat")
async def chat_with_repo(request_data: ChatRequest, req: Request):
    client_ip = req.client.host if req.client else "127.0.0.1"
    rate_limiter.check(client_ip, action="chat")

    generator = chat_service.stream_chat_sse(
        owner=request_data.owner,
        repo=request_data.repo,
        sha=request_data.sha or "latest",
        question=request_data.question,
        history=request_data.history,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
