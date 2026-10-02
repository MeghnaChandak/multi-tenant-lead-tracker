import json

import pytest

from app.ws.manager import ConnectionManager


class FakeWebSocket:
    """Minimal stand-in for fastapi.WebSocket — just enough to test the
    manager's fan-out and presence logic without a real network socket."""

    def __init__(self):
        self.sent: list[str] = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, text: str):
        self.sent.append(text)


@pytest.mark.asyncio
async def test_connect_and_broadcast_reaches_all_tenant_sockets():
    manager = ConnectionManager()
    ws_a = FakeWebSocket()
    ws_b = FakeWebSocket()

    await manager.connect(ws_a, tenant_id=1, user_id=10)
    await manager.connect(ws_b, tenant_id=1, user_id=20)

    await manager._broadcast_to_tenant(1, {"type": "test", "value": 42})

    assert len(ws_a.sent) == 1
    assert len(ws_b.sent) == 1
    assert json.loads(ws_a.sent[0])["value"] == 42


@pytest.mark.asyncio
async def test_broadcast_does_not_cross_tenants():
    manager = ConnectionManager()
    ws_tenant_1 = FakeWebSocket()
    ws_tenant_2 = FakeWebSocket()

    await manager.connect(ws_tenant_1, tenant_id=1, user_id=10)
    await manager.connect(ws_tenant_2, tenant_id=2, user_id=20)

    await manager._broadcast_to_tenant(1, {"type": "test"})

    assert len(ws_tenant_1.sent) == 1
    assert len(ws_tenant_2.sent) == 0  # tenant 2's socket must never see tenant 1's event


@pytest.mark.asyncio
async def test_presence_tracks_viewers_and_clears_on_disconnect():
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.connect(ws, tenant_id=1, user_id=10)

    await manager.mark_viewing(tenant_id=1, lead_id=99, user_id=10)
    assert manager.presence[1][99] == {10}

    # Presence broadcast was sent
    payload = json.loads(ws.sent[-1])
    assert payload["type"] == "presence"
    assert payload["viewers"] == [10]

    manager.disconnect(ws)
    assert 10 not in manager.presence[1][99]
