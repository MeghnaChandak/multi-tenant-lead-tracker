import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket

from app.ws.events import (
    ConflictWarningEvent,
    LeadChangedEvent,
    PipelineUpdatedEvent,
    PresenceEvent,
)


class ConnectionManager:
    """
    Owns:
      - active_connections: which sockets belong to which tenant room
      - presence: which user_ids are currently viewing which lead, per tenant
      - the main event loop reference, so sync route handlers (running in
        FastAPI's thread pool) can safely schedule an async broadcast
    Presence is intentionally in-memory only — never persisted to the DB —
    since it's a "right now" fact, not a historical one.
    """

    def __init__(self):
        self.active_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self.socket_user: dict[WebSocket, int] = {}
        self.socket_tenant: dict[WebSocket, int] = {}
        # tenant_id -> lead_id -> set of user_ids currently viewing
        self.presence: dict[int, dict[int, set[int]]] = defaultdict(lambda: defaultdict(set))
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop):
        """Called once at app startup so sync code can schedule broadcasts."""
        self._loop = loop

    async def connect(self, websocket: WebSocket, tenant_id: int, user_id: int):
        await websocket.accept()
        self.active_connections[tenant_id].add(websocket)
        self.socket_user[websocket] = user_id
        self.socket_tenant[websocket] = tenant_id

    def disconnect(self, websocket: WebSocket):
        tenant_id = self.socket_tenant.pop(websocket, None)
        user_id = self.socket_user.pop(websocket, None)
        if tenant_id is not None:
            self.active_connections[tenant_id].discard(websocket)
            if user_id is not None:
                # Clear this user's presence on every lead they were viewing
                for viewers in self.presence[tenant_id].values():
                    viewers.discard(user_id)

    async def _broadcast_to_tenant(self, tenant_id: int, payload: dict):
        dead = []
        for ws in self.active_connections[tenant_id]:
            try:
                await ws.send_text(json.dumps(payload))
            except (RuntimeError, ConnectionError):
                # Socket already closed or in a bad state — drop it from
                # the room rather than letting one dead connection break
                # the broadcast for everyone else.
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def broadcast_threadsafe(self, tenant_id: int, payload: dict):
        """Called from sync code (FastAPI's thread pool). Schedules the
        actual async send onto the main event loop without blocking the
        calling thread."""
        if self._loop is None:
            return  # no loop bound yet (e.g. during tests) — safe no-op
        asyncio.run_coroutine_threadsafe(
            self._broadcast_to_tenant(tenant_id, payload), self._loop
        )

    def notify_lead_changed(self, *, tenant_id: int, lead_id: int, status_code: str, assigned_to: int | None, changed_by: int):
        event = LeadChangedEvent(
            lead_id=lead_id, status_code=status_code, assigned_to=assigned_to, changed_by=changed_by
        )
        self.broadcast_threadsafe(tenant_id, event.model_dump())

    def notify_pipeline_updated(self, *, tenant_id: int, by_status: dict[str, int], total: int):
        event = PipelineUpdatedEvent(by_status=by_status, total=total)
        self.broadcast_threadsafe(tenant_id, event.model_dump())

    def notify_conflict(self, *, tenant_id: int, lead_id: int):
        """Sent when someone's stale-version write was rejected — lets
        anyone else currently viewing that lead know to reload."""
        event = ConflictWarningEvent(lead_id=lead_id)
        self.broadcast_threadsafe(tenant_id, event.model_dump())

    # ---- Presence (called from the async websocket handler directly) ----

    async def mark_viewing(self, tenant_id: int, lead_id: int, user_id: int):
        self.presence[tenant_id][lead_id].add(user_id)
        await self._broadcast_presence(tenant_id, lead_id)

    async def mark_left(self, tenant_id: int, lead_id: int, user_id: int):
        self.presence[tenant_id][lead_id].discard(user_id)
        await self._broadcast_presence(tenant_id, lead_id)

    async def _broadcast_presence(self, tenant_id: int, lead_id: int):
        viewers = sorted(self.presence[tenant_id][lead_id])
        event = PresenceEvent(lead_id=lead_id, viewers=viewers)
        await self._broadcast_to_tenant(tenant_id, event.model_dump())


# Single shared instance for the whole app
manager = ConnectionManager()
