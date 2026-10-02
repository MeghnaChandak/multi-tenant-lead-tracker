from pydantic import BaseModel


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class BillingStatusResponse(BaseModel):
    subscription_status: str
    stripe_customer_id: str | None
