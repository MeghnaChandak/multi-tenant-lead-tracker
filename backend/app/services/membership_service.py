from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.tenant import Tenant
from app.repositories.membership_repository import create_membership, get_membership
from app.repositories.tenant_repository import create_tenant
from app.repositories.user_repository import get_user_by_email


def create_tenant_with_owner(db: Session, name: str, owner_user_id: int) -> Tenant:
    tenant = create_tenant(db, name=name)
    create_membership(db, user_id=owner_user_id, tenant_id=tenant.id, role="owner")
    return tenant


def invite_member(db: Session, tenant_id: int, email: str, role: str) -> Membership:
    invitee = get_user_by_email(db, email)
    if invitee is None:
        # MVP: the invitee must already have an account (self-registered).
        # A production version would send an email invite/signup link instead.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for that email — ask them to register first",
        )

    if get_membership(db, user_id=invitee.id, tenant_id=tenant_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member of this workspace")

    return create_membership(db, user_id=invitee.id, tenant_id=tenant_id, role=role)
