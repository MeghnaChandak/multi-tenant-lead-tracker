from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories import lead_repository
from tests.conftest import make_tenant_with_users


def test_cross_tenant_lead_access_returns_none(db_session):
    tenant_1_ctx = make_tenant_with_users(db_session)

    # A second, completely separate tenant
    tenant_2 = Tenant(name="Other Co", slug="other-co", subscription_status="active")
    db_session.add(tenant_2)
    db_session.commit()
    db_session.refresh(tenant_2)

    user_2 = User(email="owner@otherco.com", hashed_password="x")
    db_session.add(user_2)
    db_session.commit()
    db_session.refresh(user_2)

    membership_2 = Membership(user_id=user_2.id, tenant_id=tenant_2.id, role="owner")
    db_session.add(membership_2)
    db_session.commit()

    # A lead that belongs to tenant 1
    lead = lead_repository.create_lead(
        db_session, tenant_id=tenant_1_ctx["tenant"].id, created_by=tenant_1_ctx["owner"].user_id,
        name="Tenant 1's lead", company=None, phone=None, email=None, source=None, next_follow_up_date=None,
    )

    # Tenant 2's owner tries to fetch it by ID, scoped to their own tenant_id
    result = lead_repository.get_lead(db_session, tenant_id=tenant_2.id, lead_id=lead.id)

    # Must be None — same as if the lead didn't exist, never leaked
    assert result is None

    # Sanity check: it's still visible correctly within its real tenant
    same_lead = lead_repository.get_lead(db_session, tenant_id=tenant_1_ctx["tenant"].id, lead_id=lead.id)
    assert same_lead is not None
    assert same_lead.id == lead.id
