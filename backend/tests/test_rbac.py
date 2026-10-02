import pytest
from fastapi import HTTPException

from app.repositories import lead_repository
from app.services import lead_service
from tests.conftest import make_tenant_with_users


def test_member_cannot_see_another_members_lead(db_session):
    ctx = make_tenant_with_users(db_session)

    # member_a creates a lead assigned to themselves
    lead = lead_repository.create_lead(
        db_session,
        tenant_id=ctx["tenant"].id,
        created_by=ctx["member_a"].user_id,
        name="Rohan Mehta",
        company="Bluewave",
        phone="9999999999",
        email=None,
        source="referral",
        next_follow_up_date=None,
    )
    lead.assigned_to = ctx["member_a"].user_id
    db_session.commit()

    # member_b tries to access it -> 403, not silently allowed
    with pytest.raises(HTTPException) as exc:
        lead_service.get_lead_or_404(db_session, membership=ctx["member_b"], lead_id=lead.id)
    assert exc.value.status_code == 403


def test_member_only_sees_own_leads_in_list(db_session):
    ctx = make_tenant_with_users(db_session)

    lead_a = lead_repository.create_lead(
        db_session, tenant_id=ctx["tenant"].id, created_by=ctx["member_a"].user_id,
        name="Lead A", company=None, phone=None, email=None, source=None, next_follow_up_date=None,
    )
    lead_a.assigned_to = ctx["member_a"].user_id
    lead_b = lead_repository.create_lead(
        db_session, tenant_id=ctx["tenant"].id, created_by=ctx["member_b"].user_id,
        name="Lead B", company=None, phone=None, email=None, source=None, next_follow_up_date=None,
    )
    lead_b.assigned_to = ctx["member_b"].user_id
    db_session.commit()

    results = lead_service.list_leads_for_membership(db_session, membership=ctx["member_a"])
    assert [lead.id for lead in results] == [lead_a.id]


def test_admin_sees_all_tenant_leads(db_session):
    ctx = make_tenant_with_users(db_session)

    for name, member in [("Lead A", ctx["member_a"]), ("Lead B", ctx["member_b"])]:
        lead = lead_repository.create_lead(
            db_session, tenant_id=ctx["tenant"].id, created_by=member.user_id,
            name=name, company=None, phone=None, email=None, source=None, next_follow_up_date=None,
        )
        lead.assigned_to = member.user_id
    db_session.commit()

    results = lead_service.list_leads_for_membership(db_session, membership=ctx["owner"])
    assert len(results) == 2
