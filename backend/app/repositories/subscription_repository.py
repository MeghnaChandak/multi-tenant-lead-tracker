from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.subscription_event import SubscriptionEvent
from app.models.tenant import Tenant


def get_event_by_stripe_id(db: Session, stripe_event_id: str) -> SubscriptionEvent | None:
    return db.query(SubscriptionEvent).filter(SubscriptionEvent.stripe_event_id == stripe_event_id).first()


def record_event(db: Session, *, tenant_id: int, stripe_event_id: str, event_type: str, payload: dict) -> SubscriptionEvent:
    """Inserts the event row unprocessed. Caller marks it processed after
    successfully applying its effect. If two webhook deliveries race each
    other, the DB's UNIQUE constraint on stripe_event_id is the real
    backstop — this function's own get-then-insert check narrows the
    window but isn't itself the guarantee."""
    event = SubscriptionEvent(
        tenant_id=tenant_id,
        stripe_event_id=stripe_event_id,
        type=event_type,
        payload_json=payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def mark_processed(db: Session, event: SubscriptionEvent):
    event.processed_at = datetime.now(timezone.utc)
    db.commit()


def update_tenant_subscription(
    db: Session,
    *,
    tenant_id: int,
    subscription_status: str,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
) -> Tenant | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None:
        return None
    tenant.subscription_status = subscription_status
    if stripe_customer_id is not None:
        tenant.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id is not None:
        tenant.stripe_subscription_id = stripe_subscription_id
    db.commit()
    db.refresh(tenant)
    return tenant


def get_tenant_by_stripe_customer_id(db: Session, stripe_customer_id: str) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.stripe_customer_id == stripe_customer_id).first()
