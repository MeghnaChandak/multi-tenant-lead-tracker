import pytest

from app.repositories import lead_repository
from app.repositories.lead_repository import StaleVersionError
from tests.conftest import make_tenant_with_users


def test_stale_version_update_raises(db_session):
    ctx = make_tenant_with_users(db_session)

    lead = lead_repository.create_lead(
        db_session, tenant_id=ctx["tenant"].id, created_by=ctx["owner"].user_id,
        name="Priya Nair", company=None, phone=None, email=None, source=None, next_follow_up_date=None,
    )
    assert lead.version == 1

    # First update succeeds, version bumps to 2
    lead_repository.update_lead(
        db_session, tenant_id=ctx["tenant"].id, lead_id=lead.id,
        expected_version=1, updated_by=ctx["owner"].user_id,
        changes={"company": "Nair Interiors"},
    )

    # A second caller who still thinks version is 1 (stale read) tries to update
    with pytest.raises(StaleVersionError):
        lead_repository.update_lead(
            db_session, tenant_id=ctx["tenant"].id, lead_id=lead.id,
            expected_version=1, updated_by=ctx["member_a"].user_id,
            changes={"company": "Overwritten Wrongly"},
        )

    # Confirm the first writer's change survived, not silently overwritten
    reloaded = lead_repository.get_lead(db_session, tenant_id=ctx["tenant"].id, lead_id=lead.id)
    assert reloaded.company == "Nair Interiors"
    assert reloaded.version == 2


def test_correct_version_update_succeeds(db_session):
    ctx = make_tenant_with_users(db_session)

    lead = lead_repository.create_lead(
        db_session, tenant_id=ctx["tenant"].id, created_by=ctx["owner"].user_id,
        name="Vikram Shah", company=None, phone=None, email=None, source=None, next_follow_up_date=None,
    )

    updated = lead_repository.update_lead(
        db_session, tenant_id=ctx["tenant"].id, lead_id=lead.id,
        expected_version=1, updated_by=ctx["owner"].user_id,
        changes={"company": "Shah Electricals"},
    )
    assert updated.version == 2
    assert updated.company == "Shah Electricals"
