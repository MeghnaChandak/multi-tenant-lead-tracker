import pytest
from fastapi import HTTPException

from app.core.dependencies import require_role
from tests.conftest import make_tenant_with_users


def test_inactive_tenant_blocked_from_subscription_gated_route(db_session):
    ctx = make_tenant_with_users(db_session)
    ctx["tenant"].subscription_status = "inactive"
    db_session.commit()

    checker = require_role("owner", "admin", "member", require_subscription=True)
    with pytest.raises(HTTPException) as exc:
        checker(membership=ctx["owner"], db=db_session)
    assert exc.value.status_code == 402


def test_active_tenant_passes_subscription_gate(db_session):
    ctx = make_tenant_with_users(db_session)
    ctx["tenant"].subscription_status = "active"
    db_session.commit()

    checker = require_role("owner", "admin", "member", require_subscription=True)
    result = checker(membership=ctx["owner"], db=db_session)
    assert result.id == ctx["owner"].id


def test_past_due_tenant_blocked(db_session):
    ctx = make_tenant_with_users(db_session)
    ctx["tenant"].subscription_status = "past_due"
    db_session.commit()

    checker = require_role("owner", "admin", "member", require_subscription=True)
    with pytest.raises(HTTPException) as exc:
        checker(membership=ctx["owner"], db=db_session)
    assert exc.value.status_code == 402


def test_billing_routes_not_subscription_gated(db_session):
    """Sanity check: an owner on an inactive tenant must still pass a
    plain role check with no subscription requirement, so they can reach
    the checkout page to fix it."""
    ctx = make_tenant_with_users(db_session)
    ctx["tenant"].subscription_status = "inactive"
    db_session.commit()

    checker = require_role("owner")  # require_subscription defaults to False
    result = checker(membership=ctx["owner"], db=db_session)
    assert result.id == ctx["owner"].id
