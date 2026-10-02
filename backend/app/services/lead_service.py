from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.models.membership import Membership
from app.repositories import lead_activity_repository, lead_repository
from app.repositories.lead_repository import StaleVersionError
from app.schemas.lead import CreateLeadRequest, DuplicateWarning, UpdateLeadRequest
from app.services import realtime_service

DUPLICATE_SIMILARITY_THRESHOLD = 0.4


def _lead_to_status_code(lead: Lead) -> str:
    return lead.status.code


def create_lead_with_duplicate_check(
    db: Session, *, membership: Membership, payload: CreateLeadRequest
) -> tuple[Lead, list[DuplicateWarning]]:
    duplicates = lead_repository.find_potential_duplicates(
        db,
        tenant_id=membership.tenant_id,
        name=payload.name,
        company=payload.company,
        phone=payload.phone,
        email=payload.email,
    )

    lead = lead_repository.create_lead(
        db,
        tenant_id=membership.tenant_id,
        created_by=membership.user_id,
        name=payload.name,
        company=payload.company,
        phone=payload.phone,
        email=payload.email,
        source=payload.source,
        next_follow_up_date=payload.next_follow_up_date,
    )

    warnings = [
        DuplicateWarning(
            lead_id=existing.id,
            name=existing.name,
            company=existing.company,
            similarity=round(score, 2),
            created_at=existing.created_at,
        )
        for existing, score in duplicates
        if score >= DUPLICATE_SIMILARITY_THRESHOLD
    ]

    summary = lead_repository.get_pipeline_summary(db, tenant_id=membership.tenant_id)
    realtime_service.broadcast_pipeline_updated(tenant_id=membership.tenant_id, summary=summary)

    return lead, warnings


def get_lead_or_404(db: Session, *, membership: Membership, lead_id: int) -> Lead:
    lead = lead_repository.get_lead(db, tenant_id=membership.tenant_id, lead_id=lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    # Members can only see/act on their own leads, even within the same tenant
    if membership.role == "member" and lead.assigned_to != membership.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lead")

    return lead


def list_leads_for_membership(db: Session, *, membership: Membership) -> list[Lead]:
    if membership.role == "member":
        return lead_repository.list_leads_for_member(
            db, tenant_id=membership.tenant_id, user_id=membership.user_id
        )
    return lead_repository.list_leads_for_tenant(db, tenant_id=membership.tenant_id)


def list_due_today_for_membership(db: Session, *, membership: Membership, today: date) -> list[Lead]:
    user_id = membership.user_id if membership.role == "member" else None
    return lead_repository.list_due_today(db, tenant_id=membership.tenant_id, user_id=user_id, today=today)


def update_lead(
    db: Session, *, membership: Membership, lead_id: int, payload: UpdateLeadRequest
) -> Lead:
    # Re-run the same visibility check before allowing an update
    get_lead_or_404(db, membership=membership, lead_id=lead_id)

    changes: dict = {}
    if payload.status_code is not None:
        changes["status_id"] = lead_repository.get_status_by_code(db, payload.status_code).id
    if payload.next_follow_up_date is not None:
        changes["next_follow_up_date"] = payload.next_follow_up_date
    if payload.name is not None:
        changes["name"] = payload.name
    if payload.company is not None:
        changes["company"] = payload.company
    if payload.phone is not None:
        changes["phone"] = payload.phone
    if payload.email is not None:
        changes["email"] = payload.email
    if payload.source is not None:
        changes["source"] = payload.source

    if payload.assigned_to is not None:
        # Only admin/owner can reassign leads between members
        if membership.role == "member":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can reassign leads")
        changes["assigned_to"] = payload.assigned_to

    try:
        updated = lead_repository.update_lead(
            db,
            tenant_id=membership.tenant_id,
            lead_id=lead_id,
            expected_version=payload.version,
            updated_by=membership.user_id,
            changes=changes,
        )
    except StaleVersionError:
        # Someone else is likely mid-edit or just saved — let anyone
        # viewing this lead know immediately, not just the requester.
        realtime_service.broadcast_conflict(tenant_id=membership.tenant_id, lead_id=lead_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This lead changed since you loaded it. Reload and try again.",
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    realtime_service.broadcast_lead_changed(updated, changed_by=membership.user_id)

    # A status or assignment change shifts the pipeline view too — recompute
    # and push it so admin dashboards update without a manual refresh.
    if "status_id" in changes or "assigned_to" in changes:
        summary = lead_repository.get_pipeline_summary(db, tenant_id=membership.tenant_id)
        realtime_service.broadcast_pipeline_updated(tenant_id=membership.tenant_id, summary=summary)

    return updated


def add_note(db: Session, *, membership: Membership, lead_id: int, note: str):
    get_lead_or_404(db, membership=membership, lead_id=lead_id)  # enforces visibility first
    return lead_activity_repository.add_activity(db, lead_id=lead_id, user_id=membership.user_id, note=note)


def get_pipeline_summary(db: Session, *, membership: Membership) -> dict:
    return lead_repository.get_pipeline_summary(db, tenant_id=membership.tenant_id)
