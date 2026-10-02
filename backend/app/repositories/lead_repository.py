from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.models.lead_status import CLOSED_STATUS_CODES, LeadStatus


class StaleVersionError(Exception):
    """Raised when an update's supplied version doesn't match the current row."""


def get_status_by_code(db: Session, code: str) -> LeadStatus:
    status = db.query(LeadStatus).filter(LeadStatus.code == code).first()
    if status is None:
        raise ValueError(f"Unknown status code: {code}")
    return status


def create_lead(
    db: Session,
    *,
    tenant_id: int,
    created_by: int,
    name: str,
    company: str | None,
    phone: str | None,
    email: str | None,
    source: str | None,
    next_follow_up_date: date | None,
) -> Lead:
    new_status = get_status_by_code(db, "new")
    lead = Lead(
        tenant_id=tenant_id,
        name=name,
        company=company,
        phone=phone,
        email=email,
        source=source,
        status_id=new_status.id,
        next_follow_up_date=next_follow_up_date,
        created_by=created_by,
        version=1,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def get_lead(db: Session, *, tenant_id: int, lead_id: int) -> Lead | None:
    """tenant_id is required, not optional — this is the enforcement point
    for cross-tenant access. A lead ID from another tenant simply returns
    None here, same as if it didn't exist."""
    return (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.tenant_id == tenant_id, Lead.is_deleted == False)
        .first()
    )


def list_leads_for_tenant(db: Session, *, tenant_id: int) -> list[Lead]:
    """Admin/owner view — all leads in the tenant."""
    return (
        db.query(Lead)
        .filter(Lead.tenant_id == tenant_id, Lead.is_deleted == False)
        .order_by(Lead.created_at.desc())
        .all()
    )


def list_leads_for_member(db: Session, *, tenant_id: int, user_id: int) -> list[Lead]:
    """Member view — only leads assigned to them, still tenant-scoped."""
    return (
        db.query(Lead)
        .filter(
            Lead.tenant_id == tenant_id,
            Lead.assigned_to == user_id,
            Lead.is_deleted == False,
        )
        .order_by(Lead.created_at.desc())
        .all()
    )


def list_due_today(db: Session, *, tenant_id: int, user_id: int | None, today: date) -> list[Lead]:
    """user_id=None → org-wide (admin/owner); otherwise scoped to that member."""
    query = (
        db.query(Lead)
        .join(LeadStatus, Lead.status_id == LeadStatus.id)
        .filter(
            Lead.tenant_id == tenant_id,
            Lead.is_deleted == False,
            Lead.next_follow_up_date <= today,
            LeadStatus.code.notin_(CLOSED_STATUS_CODES),
        )
    )
    if user_id is not None:
        query = query.filter(Lead.assigned_to == user_id)
    return query.order_by(Lead.next_follow_up_date.asc()).all()


def update_lead(
    db: Session,
    *,
    tenant_id: int,
    lead_id: int,
    expected_version: int,
    updated_by: int,
    changes: dict,
) -> Lead:
    """Optimistic-locked update, scoped to tenant_id. Raises StaleVersionError
    if expected_version doesn't match the row currently in the DB — the
    caller (service layer) turns that into an HTTP 409."""
    lead = get_lead(db, tenant_id=tenant_id, lead_id=lead_id)
    if lead is None:
        raise ValueError("Lead not found")

    if lead.version != expected_version:
        raise StaleVersionError(f"Expected version {expected_version}, current is {lead.version}")

    for field, value in changes.items():
        setattr(lead, field, value)

    lead.version += 1
    lead.updated_by = updated_by
    db.commit()
    db.refresh(lead)
    return lead


def find_potential_duplicates(
    db: Session, *, tenant_id: int, name: str, company: str | None, phone: str | None, email: str | None
) -> list[tuple[Lead, float]]:
    """Exact match on phone/email, fuzzy match on name/company using
    Postgres trigram similarity (pg_trgm extension). Returns (lead, score)
    pairs above threshold, highest similarity first."""
    results: dict[int, float] = {}
    exact_phone: list[Lead] = []
    exact_email: list[Lead] = []

    if phone:
        exact_phone = (
            db.query(Lead)
            .filter(Lead.tenant_id == tenant_id, Lead.is_deleted == False, Lead.phone == phone)
            .all()
        )
        for lead in exact_phone:
            results[lead.id] = max(results.get(lead.id, 0), 1.0)

    if email:
        exact_email = (
            db.query(Lead)
            .filter(Lead.tenant_id == tenant_id, Lead.is_deleted == False, Lead.email == email)
            .all()
        )
        for lead in exact_email:
            results[lead.id] = max(results.get(lead.id, 0), 1.0)

    # Fuzzy match on name via pg_trgm's similarity() function
    fuzzy_matches = (
        db.query(Lead, func.similarity(Lead.name, name).label("sim"))
        .filter(
            Lead.tenant_id == tenant_id,
            Lead.is_deleted == False,
            func.similarity(Lead.name, name) > 0.4,
        )
        .order_by(func.similarity(Lead.name, name).desc())
        .limit(5)
        .all()
    )
    for lead, sim in fuzzy_matches:
        results[lead.id] = max(results.get(lead.id, 0), float(sim))

    id_to_lead = {lead.id: lead for lead in exact_phone}
    id_to_lead.update({lead.id: lead for lead in exact_email})
    id_to_lead.update({lead.id: lead for lead, _ in fuzzy_matches})

    return sorted(
        [(id_to_lead[lid], score) for lid, score in results.items() if lid in id_to_lead],
        key=lambda pair: pair[1],
        reverse=True,
    )


def get_pipeline_summary(db: Session, *, tenant_id: int) -> dict:
    rows = (
        db.query(LeadStatus.code, func.count(Lead.id))
        .join(Lead, Lead.status_id == LeadStatus.id)
        .filter(Lead.tenant_id == tenant_id, Lead.is_deleted == False)
        .group_by(LeadStatus.code)
        .all()
    )
    by_status = {code: count for code, count in rows}
    total = sum(by_status.values())
    won = by_status.get("won", 0)
    lost = by_status.get("lost", 0)
    closed = won + lost
    conversion_rate = round((won / closed) * 100, 1) if closed > 0 else 0.0

    return {
        "by_status": by_status,
        "total": total,
        "won": won,
        "lost": lost,
        "conversion_rate": conversion_rate,
    }
