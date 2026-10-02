from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import require_role
from app.database import get_db
from app.models.membership import Membership
from app.repositories.tenant_repository import get_tenant
from app.schemas.billing import BillingStatusResponse, CheckoutSessionResponse
from app.services import billing_service

router = APIRouter(tags=["billing"])


@router.post("/tenants/{tenant_id}/billing/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session_route(
    membership: Membership = Depends(require_role("owner")),  # deliberately no require_subscription
    db: Session = Depends(get_db),
):
    checkout_url = billing_service.create_checkout_session(
        db,
        membership=membership,
        success_url=f"{settings.frontend_origin}/billing/success",
        cancel_url=f"{settings.frontend_origin}/billing/cancelled",
    )
    return CheckoutSessionResponse(checkout_url=checkout_url)


@router.get("/tenants/{tenant_id}/billing-status", response_model=BillingStatusResponse)
def billing_status_route(
    membership: Membership = Depends(require_role("owner", "admin", "member")),  # no subscription gate — everyone can see status
    db: Session = Depends(get_db),
):
    tenant = get_tenant(db, membership.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return BillingStatusResponse(
        subscription_status=tenant.subscription_status,
        stripe_customer_id=tenant.stripe_customer_id,
    )


@router.post("/webhooks/stripe", status_code=200)
async def stripe_webhook_route(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    event = billing_service.verify_and_parse_webhook(payload, sig_header)
    billing_service.handle_webhook_event(db, event)

    # Always 200 once verified + processed (or already-processed no-op) —
    # returning anything else makes Stripe retry indefinitely.
    return {"received": True}
