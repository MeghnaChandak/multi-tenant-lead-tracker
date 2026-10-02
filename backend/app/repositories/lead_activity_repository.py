from sqlalchemy.orm import Session

from app.models.lead_activity import LeadActivity


def add_activity(db: Session, *, lead_id: int, user_id: int, note: str) -> LeadActivity:
    activity = LeadActivity(lead_id=lead_id, user_id=user_id, note=note)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_activity_for_lead(db: Session, *, lead_id: int) -> list[LeadActivity]:
    return (
        db.query(LeadActivity)
        .filter(LeadActivity.lead_id == lead_id)
        .order_by(LeadActivity.created_at.desc())
        .all()
    )
