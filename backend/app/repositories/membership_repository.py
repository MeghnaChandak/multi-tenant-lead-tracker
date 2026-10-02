from sqlalchemy.orm import Session

from app.models.membership import Membership


def create_membership(db: Session, user_id: int, tenant_id: int, role: str) -> Membership:
    membership = Membership(user_id=user_id, tenant_id=tenant_id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def get_membership(db: Session, user_id: int, tenant_id: int) -> Membership | None:
    return (
        db.query(Membership)
        .filter(
            Membership.user_id == user_id,
            Membership.tenant_id == tenant_id,
            Membership.is_deleted == False,
        )
        .first()
    )


def list_members(db: Session, tenant_id: int) -> list[Membership]:
    return (
        db.query(Membership)
        .filter(Membership.tenant_id == tenant_id, Membership.is_deleted == False)
        .all()
    )
