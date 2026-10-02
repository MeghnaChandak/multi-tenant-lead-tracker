import jwt
from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodes the access token and loads the user. Never trusts any claim
    beyond 'who is this user' — tenant/role are resolved separately, per
    request, from the DB (see get_membership below)."""
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_membership(
    tenant_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    """The single place that answers 'is this user actually in this tenant,
    and what role do they hold there'. tenant_id always comes from the URL
    path, checked against the DB — never from a client-supplied header or
    an embedded JWT claim, since a user may belong to more than one tenant."""
    membership = (
        db.query(Membership)
        .filter(
            Membership.user_id == current_user.id,
            Membership.tenant_id == tenant_id,
            Membership.is_deleted == False,
        )
        .first()
    )
    if membership is None:
        # 404, not 403 — don't reveal whether the tenant exists to a non-member
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return membership


def require_role(*allowed_roles: str, require_subscription: bool = False):
    """Usage: Depends(require_role('owner', 'admin')) for a plain role check.
    Pass require_subscription=True for routes that are actual product
    features (leads, pipeline) — these are blocked if the tenant's
    subscription isn't active. Billing and membership-management routes
    deliberately leave this False, so an owner with a lapsed subscription
    can still reach the checkout page to fix it."""

    def checker(
        membership: Membership = Depends(get_membership),
        db: Session = Depends(get_db),
    ) -> Membership:
        if membership.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action")

        if require_subscription:
            tenant = db.query(Tenant).filter(Tenant.id == membership.tenant_id).first()
            if tenant is None or tenant.subscription_status != "active":
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="This workspace's subscription is not active",
                )

        return membership

    return checker
