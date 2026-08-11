from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    select,
    String,
    Integer,
    ForeignKey,
    DateTime,
    func,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, get_db
from .user import User
from .jobs import JobOffer
from .auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

# === MODELS ===

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_offers.id"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    read_at: Mapped[Optional["DateTime"]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    job: Mapped["JobOffer"] = relationship() # Add to imports
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship(foreign_keys=[receiver_id])


# === SCHEMAS ===

class MessageOut(BaseModel):
    id: int
    job_id: int
    sender_id: int
    receiver_id: int
    content: str
    attachments: Optional[List[str]]
    created_at: datetime
    read_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    job_id: int
    receiver_id: int
    content: str
    attachments: Optional[List[str]] = None


# === WEBSOCKET MANAGER ===

class ConnectionManager:
    def __init__(self):
        # active_connections: user_id -> List[WebSocket]
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

manager = ConnectionManager()


# === ENDPOINTS ===

@router.get("/history/{job_id}", response_model=List[MessageOut])
async def get_chat_history(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get chat history for a specific job.
    User must be either the client (owner of job) or the worker (applicant/assigned).
    For MVP, we check if user is participant in messages or job relation.
    """
    # Simple check: user must be sender or receiver in messages of this job
    # OR we check job ownership / application accepted.
    # Check job participants roughly:
    job = await db.get(JobOffer, job_id)
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")

    # If I am client, I can see messages for this job
    # If I am worker, I can see messages for this job WHERE I am sender/receiver
    
    query = select(Message).where(Message.job_id == job_id)
    
    if current_user.id == job.client_id:
        # Client sees all messages related to this job?
        # Actually client might chat with multiple workers.
        # But MVP: chat room is per job/worker pair?
        # Requirements: "Salons chat : unique par job+travailleur+client"
        # So fetching history needs filter by counterparty if I am client?
        # For simple history, let's just return all messages where I am sender or receiver.
         pass
    else:
        # Worker logic
        pass

    query = query.where(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    )
    query = query.order_by(Message.created_at.asc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Connect with /chat/ws?token=<jwt access token>. The user identity is derived
    from the token (not a client-supplied id), so a client can only ever receive
    messages addressed to themselves.
    """
    from jose import JWTError, jwt
    from .config import settings

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        await websocket.close(code=4401)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            # Messages are sent via the REST endpoint below and pushed out over
            # this socket; we just keep the connection alive and drain pings.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.post("", response_model=MessageOut)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Save to DB
    msg = Message(
        job_id=data.job_id,
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        content=data.content,
        attachments=data.attachments
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    
    # 2. Push to receiver via WebSocket
    import json
    payload = {
        "type": "new_message",
        "data": {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "job_id": msg.job_id,
            "created_at": msg.created_at.isoformat()
        }
    }
    await manager.send_personal_message(json.dumps(payload), data.receiver_id)
    
    return msg
