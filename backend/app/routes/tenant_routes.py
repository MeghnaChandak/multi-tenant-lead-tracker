from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.membership import Membership
from app.models.user import User
from app.repositories.membership_repository import list_members
from app.schemas.tenant import (
    CreateTenantRequest,
    InviteMemberRequest,
    MembershipResponse,
    TenantResponse,
)
from app.services.membership_service import create_tenant_with_owner, invite_member
from app.models.tenant import Tenant


router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=201)
def create_tenant_route(
    payload: CreateTenantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant = create_tenant_with_owner(db, name=payload.name, owner_user_id=current_user.id)
    return tenant


@router.post("/{tenant_id}/invite", response_model=MembershipResponse, status_code=201)
def invite_member_route(
    payload: InviteMemberRequest,
    membership: Membership = Depends(require_role("owner", "admin")),
    db: Session = Depends(get_db),
):
    new_membership = invite_member(db, tenant_id=membership.tenant_id, email=payload.email, role=payload.role)
    return new_membership


@router.get("/{tenant_id}/members", response_model=list[MembershipResponse])
def list_members_route(
    membership: Membership = Depends(require_role("owner", "admin", "member")),
    db: Session = Depends(get_db),
):
    return list_members(db, tenant_id=membership.tenant_id)

@router.get("/me/tenants")
def my_tenants_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = (
        db.query(Membership, Tenant)
        .join(Tenant, Tenant.id == Membership.tenant_id)
        .filter(Membership.user_id == current_user.id, Membership.is_deleted == False)
        .all()
    )
    return [
        {"tenant_id": tenant.id, "tenant_name": tenant.name, "role": membership.role}
        for membership, tenant in memberships
    ]