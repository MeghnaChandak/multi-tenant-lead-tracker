import json

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.security import decode_token
from app.database import SessionLocal
from app.models.membership import Membership
from app.models.user import User
from app.ws.events import LeaveLeadMessage, ViewLeadMessage
from app.ws.manager import manager

router = APIRouter(tags=["websocket"])


def _authenticate(token: str, tenant_id: int) -> int | None:
    """Returns the authenticated user_id if the token is valid AND that
    user actually belongs to this tenant — never trusts tenant_id from
    the client beyond using it to check real membership. Returns None on
    any failure; caller closes the socket."""
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        return None

    if payload.get("type") != "access":
        return None

    user_id = int(payload["sub"])

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if user is None:
            return None
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user_id,
                Membership.tenant_id == tenant_id,
                Membership.is_deleted == False,
            )
            .first()
        )
        if membership is None:
            return None
        return user_id
    finally:
        db.close()


@router.websocket("/ws/tenant/{tenant_id}")
async def tenant_websocket(websocket: WebSocket, tenant_id: int, token: str = Query(...)):
    user_id = _authenticate(token, tenant_id)
    if user_id is None:
        # Reject before accept() — never open the socket for an unauthenticated
        # or non-member caller, and never let the client dictate its own room.
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, tenant_id=tenant_id, user_id=user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            if msg_type == "view_lead":
                msg = ViewLeadMessage(**data)
                await manager.mark_viewing(tenant_id, msg.lead_id, user_id)
            elif msg_type == "leave_lead":
                msg = LeaveLeadMessage(**data)
                await manager.mark_left(tenant_id, msg.lead_id, user_id)
            # Unknown message types are silently ignored rather than
            # crashing the connection — keeps the protocol forward-compatible.
    except WebSocketDisconnect:
        manager.disconnect(websocket)
