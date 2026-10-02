"""
These tests exercise the websocket route's authentication logic directly
(the _authenticate function) against the same SQLite fixture used
elsewhere, rather than spinning up the full ASGI app over a real socket
-- that needs the Postgres-backed app running, which isn't available in
this sandbox. The full connect/broadcast/presence flow is exercised
manually against a real Postgres instance before deployment (documented
in the README's "how to verify" section).
"""

import app.routes.websocket_routes as ws_routes
from app.core.security import create_access_token
from app.routes.websocket_routes import _authenticate
from tests.conftest import make_tenant_with_users


def test_valid_member_token_authenticates(monkeypatch, db_session):
    ctx = make_tenant_with_users(db_session)
    monkeypatch.setattr(ws_routes, "SessionLocal", lambda: db_session)
    # SQLAlchemy session.close() would break the shared test session; no-op it
    monkeypatch.setattr(db_session, "close", lambda: None)

    token = create_access_token(ctx["owner"].user_id)
    result = _authenticate(token, ctx["tenant"].id)
    assert result == ctx["owner"].user_id


def test_non_member_token_rejected(monkeypatch, db_session):
    ctx = make_tenant_with_users(db_session)
    monkeypatch.setattr(ws_routes, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    # A second tenant this user has no membership in
    from app.models.tenant import Tenant
    other_tenant = Tenant(name="Other", slug="other", subscription_status="active")
    db_session.add(other_tenant)
    db_session.commit()
    db_session.refresh(other_tenant)

    token = create_access_token(ctx["owner"].user_id)
    result = _authenticate(token, other_tenant.id)
    assert result is None


def test_garbage_token_rejected(db_session):
    result = _authenticate("not-a-real-jwt", tenant_id=1)
    assert result is None
