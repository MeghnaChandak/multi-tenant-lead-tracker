from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.membership import Membership
from app.schemas.lead import (
    ActivityResponse,
    AddActivityRequest,
    CreateLeadRequest,
    CreateLeadResponse,
    LeadResponse,
    PipelineSummaryResponse,
    UpdateLeadRequest,
)
from app.services import lead_service

router = APIRouter(prefix="/tenants/{tenant_id}/leads", tags=["leads"])


def _to_lead_response(lead) -> LeadResponse:
    return LeadResponse(
        id=lead.id,
        tenant_id=lead.tenant_id,
        name=lead.name,
        company=lead.company,
        phone=lead.phone,
        email=lead.email,
        source=lead.source,
        status_code=lead.status.code,
        assigned_to=lead.assigned_to,
        next_follow_up_date=lead.next_follow_up_date,
        version=lead.version,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.post("", response_model=CreateLeadResponse, status_code=201)
def create_lead_route(
    payload: CreateLeadRequest,
    membership: Membership = Depends(require_role("owner", "admin", "member", require_subscription=True)),
    db: Session = Depends(get_db),
):
    lead, duplicates = lead_service.create_lead_with_duplicate_check(db, membership=membership, payload=payload)
    return CreateLeadResponse(lead=_to_lead_response(lead), possible_duplicates=duplicates)


@router.get("", response_model=list[LeadResponse])
def list_leads_route(
    membership: Membership = Depends(require_role("owner", "admin", "member", require_subscription=True)),
    db: Session = Depends(get_db),
):
    leads = lead_service.list_leads_for_membership(db, membership=membership)
    return [_to_lead_response(lead) for lead in leads]


@router.get("/due-today", response_model=list[LeadResponse])
def due_today_route(
    membership: Membership = Depends(require_role("owner", "admin", "member", require_subscription=True)),
    db: Session = Depends(get_db),
):
    leads = lead_service.list_due_today_for_membership(db, membership=membership, today=date.today())
    return [_to_lead_response(lead) for lead in leads]


@router.get("/pipeline-summary", response_model=PipelineSummaryResponse)
def pipeline_summary_route(
    membership: Membership = Depends(require_role("owner", "admin", require_subscription=True)),
    db: Session = Depends(get_db),
):
    summary = lead_service.get_pipeline_summary(db, membership=membership)
    return PipelineSummaryResponse(**summary)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead_route(
    lead_id: int,
    payload: UpdateLeadRequest,
    membership: Membership = Depends(require_role("owner", "admin", "member", require_subscription=True)),
    db: Session = Depends(get_db),
):
    lead = lead_service.update_lead(db, membership=membership, lead_id=lead_id, payload=payload)
    return _to_lead_response(lead)


@router.post("/{lead_id}/activity", response_model=ActivityResponse, status_code=201)
def add_activity_route(
    lead_id: int,
    payload: AddActivityRequest,
    membership: Membership = Depends(require_role("owner", "admin", "member", require_subscription=True)),
    db: Session = Depends(get_db),
):
    activity = lead_service.add_note(db, membership=membership, lead_id=lead_id, note=payload.note)
    return activity
