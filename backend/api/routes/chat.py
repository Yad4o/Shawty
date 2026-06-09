"""
Chat endpoint — core agent interaction.
Accepts a user message + session_id, runs the agent loop, returns the response.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.agent.controller import AgentController
from backend.database.connection import get_db
from backend.database.models import Message
from backend.llm.client import OllamaClient
from backend.tools.registry import ToolRegistry

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[dict] = []
    iterations: int = 0


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message to the OmClaw agent and receive a response."""

    # Load conversation history
    result = await db.execute(
        select(Message)
        .where(Message.session_id == req.session_id)
        .order_by(Message.created_at.asc())
        .limit(50)
    )
    history_msgs = result.scalars().all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]

    # Initialize agent
    llm = OllamaClient()
    tools = ToolRegistry()
    tools.register_defaults()
    agent = AgentController(llm=llm, tools=tools)

    # Run agent
    result_data = await agent.run(user_message=req.message, history=history)
    await llm.close()

    # Persist messages
    user_msg = Message(session_id=req.session_id, role="user", content=req.message)
    assistant_msg = Message(
        session_id=req.session_id,
        role="assistant",
        content=result_data["response"],
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.flush()

    return ChatResponse(
        response=result_data["response"],
        tool_calls=result_data["tool_calls"],
        iterations=result_data["iterations"],
    )
