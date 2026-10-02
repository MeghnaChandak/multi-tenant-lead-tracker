import stripe
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.membership import Membership
from app.repositories import subscription_repository, tenant_repository

stripe.api_key = settings.stripe_secret_key

# Events we actively react to. Anything else is stored (for audit) but
# not acted on — Stripe sends many event types we don't need yet.
HANDLED_EVENT_TYPES = {
    "checkout.session.completed",
    "invoice.payment_failed",
    "customer.subscription.deleted",
}


def create_checkout_session(db: Session, *, membership: Membership, success_url: str, cancel_url: str) -> str:
    """Owner-only (enforced by the route's require_role). Price and product
    are always decided server-side from settings — the client never sends
    an amount or price ID."""
    tenant = tenant_repository.get_tenant(db, membership.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    session_kwargs = {
        "mode": "subscription",
        "line_items": [{"price": settings.stripe_price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(tenant.id),
        "metadata": {"tenant_id": str(tenant.id)},
    }
    if tenant.stripe_customer_id:
        session_kwargs["customer"] = tenant.stripe_customer_id
    else:
        session_kwargs["customer_email"] = None  # let Stripe collect it on the hosted page

    session = stripe.checkout.Session.create(**session_kwargs)
    return session.url


def verify_and_parse_webhook(payload: bytes, sig_header: str) -> stripe.Event:
    """Raises HTTPException(400) if the signature doesn't check out. This
    must run before any of the event's contents are trusted or acted on."""
    try:
        return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")


def handle_webhook_event(db: Session, event: stripe.Event) -> None:
    """Idempotent: if this stripe_event_id was already recorded, do
    nothing and return success — Stripe redelivers events, sometimes more
    than once, and the caller (route) always returns 200 either way so
    Stripe doesn't keep retrying a webhook we've already handled."""
    existing = subscription_repository.get_event_by_stripe_id(db, event["id"])
    if existing is not None:
        return  # already processed (or in flight) — no-op

    data_object = event["data"]["object"]
    tenant_id = _resolve_tenant_id(db, event, data_object)

    try:
        record = subscription_repository.record_event(
            db,
            tenant_id=tenant_id,
            stripe_event_id=event["id"],
            event_type=event["type"],
            payload=dict(data_object),
        )
    except IntegrityError:
        # A concurrent delivery of the same event won the race and inserted
        # first. This is the real backstop — the get-check above only
        # narrows the window, it doesn't close it. Roll back and no-op.
        db.rollback()
        return

    if event["type"] not in HANDLED_EVENT_TYPES:
        subscription_repository.mark_processed(db, record)
        return

    if event["type"] == "checkout.session.completed":
        subscription_repository.update_tenant_subscription(
            db,
            tenant_id=tenant_id,
            subscription_status="active",
            stripe_customer_id=data_object.get("customer"),
            stripe_subscription_id=data_object.get("subscription"),
        )

    elif event["type"] == "invoice.payment_failed":
        subscription_repository.update_tenant_subscription(db, tenant_id=tenant_id, subscription_status="past_due")

    elif event["type"] == "customer.subscription.deleted":
        subscription_repository.update_tenant_subscription(db, tenant_id=tenant_id, subscription_status="canceled")

    subscription_repository.mark_processed(db, record)


def _resolve_tenant_id(db: Session, event: stripe.Event, data_object: dict) -> int:
    """Never trust a tenant_id sent verbatim in the payload without
    resolving it through something we control. For checkout.session.completed
    we set client_reference_id/metadata ourselves at session-creation time,
    so it's trustworthy. For later lifecycle events (which reference a
    customer, not our metadata), resolve via the customer ID we stored."""
    metadata = data_object.get("metadata") or {}
    if "tenant_id" in metadata:
        return int(metadata["tenant_id"])

    client_ref = data_object.get("client_reference_id")
    if client_ref:
        return int(client_ref)

    customer_id = data_object.get("customer")
    if customer_id:
        tenant = subscription_repository.get_tenant_by_stripe_customer_id(db, customer_id)
        if tenant:
            return tenant.id

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not resolve tenant for this event")
