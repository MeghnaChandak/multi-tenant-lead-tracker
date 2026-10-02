
from app.services import billing_service
from tests.conftest import make_tenant_with_users


def _fake_checkout_completed_event(event_id: str, tenant_id: int, customer_id: str = "cus_123"):
    """Mimics the shape of a stripe.Event enough for handle_webhook_event
    to process it — real signature verification is tested separately."""
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": customer_id,
                "subscription": "sub_abc",
                "client_reference_id": str(tenant_id),
                "metadata": {"tenant_id": str(tenant_id)},
            }
        },
    }


def test_duplicate_webhook_delivery_is_processed_once(db_session):
    ctx = make_tenant_with_users(db_session)
    ctx["tenant"].subscription_status = "inactive"
    db_session.commit()

    event = _fake_checkout_completed_event("evt_test_1", ctx["tenant"].id)

    # First delivery activates the tenant
    billing_service.handle_webhook_event(db_session, event)
    db_session.refresh(ctx["tenant"])
    assert ctx["tenant"].subscription_status == "active"

    from app.models.subscription_event import SubscriptionEvent
    count_after_first = db_session.query(SubscriptionEvent).filter(
        SubscriptionEvent.stripe_event_id == "evt_test_1"
    ).count()
    assert count_after_first == 1

    # Second delivery of the SAME event (Stripe retries) — must be a no-op
    billing_service.handle_webhook_event(db_session, event)

    count_after_second = db_session.query(SubscriptionEvent).filter(
        SubscriptionEvent.stripe_event_id == "evt_test_1"
    ).count()
    assert count_after_second == 1  # still exactly one row, not two


def test_payment_failed_marks_tenant_past_due(db_session):
    ctx = make_tenant_with_users(db_session)
    ctx["tenant"].subscription_status = "active"
    ctx["tenant"].stripe_customer_id = "cus_456"
    db_session.commit()

    event = {
        "id": "evt_test_2",
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": "cus_456"}},
    }
    billing_service.handle_webhook_event(db_session, event)
    db_session.refresh(ctx["tenant"])
    assert ctx["tenant"].subscription_status == "past_due"


def test_subscription_deleted_marks_tenant_canceled(db_session):
    ctx = make_tenant_with_users(db_session)
    ctx["tenant"].subscription_status = "active"
    ctx["tenant"].stripe_customer_id = "cus_789"
    db_session.commit()

    event = {
        "id": "evt_test_3",
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_789"}},
    }
    billing_service.handle_webhook_event(db_session, event)
    db_session.refresh(ctx["tenant"])
    assert ctx["tenant"].subscription_status == "canceled"


def test_unresolvable_tenant_raises(db_session):
    import pytest
    from fastapi import HTTPException

    event = {
        "id": "evt_test_4",
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": "cus_does_not_exist"}},
    }
    with pytest.raises(HTTPException) as exc:
        billing_service.handle_webhook_event(db_session, event)
    assert exc.value.status_code == 400
