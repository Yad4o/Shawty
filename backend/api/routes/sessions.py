"""Session management endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.connection import get_db
from backend.database.models import Session as DBSession

router = APIRouter()


class CreateSessionRequest(BaseModel):
    title: str | None = None
    workspace_path: str | None = None


@router.post("/")
async def create_session(req: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    session = DBSession(id=str(uuid.uuid4()), title=req.title, workspace_path=req.workspace_path)
    db.add(session)
    await db.flush()
    return {"session_id": session.id, "title": session.title}


@router.get("/")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBSession).order_by(DBSession.created_at.desc()).limit(50))
    sessions = result.scalars().all()
    return [{"id": s.id, "title": s.title, "created_at": str(s.created_at)} for s in sessions]


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBSession).where(DBSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": session.id, "title": session.title, "workspace_path": session.workspace_path}
