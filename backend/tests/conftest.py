import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (  # noqa: F401
    lead,
    lead_activity,
    lead_status,
    membership,
    tenant,
    user,
)
from app.models.lead_status import SEED_STATUSES, LeadStatus
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User


@pytest.fixture()
def db_session():
    # SQLite in-memory for fast, dependency-free unit tests. Note: SQLite
    # doesn't support pg_trgm, so fuzzy-duplicate tests run separately
    # against a real Postgres instance (see test_duplicate_detection.py).
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    for s in SEED_STATUSES:
        session.add(LeadStatus(**s))
    session.commit()
    yield session
    session.close()


def make_tenant_with_users(db):
    """Helper: one tenant, one owner, two members (A and B)."""
    t = Tenant(name="Acme", slug="acme", subscription_status="active")
    db.add(t)
    db.commit()
    db.refresh(t)

    owner = User(email="owner@acme.com", hashed_password="x")
    member_a = User(email="a@acme.com", hashed_password="x")
    member_b = User(email="b@acme.com", hashed_password="x")
    db.add_all([owner, member_a, member_b])
    db.commit()
    for u in (owner, member_a, member_b):
        db.refresh(u)

    m_owner = Membership(user_id=owner.id, tenant_id=t.id, role="owner")
    m_a = Membership(user_id=member_a.id, tenant_id=t.id, role="member")
    m_b = Membership(user_id=member_b.id, tenant_id=t.id, role="member")
    db.add_all([m_owner, m_a, m_b])
    db.commit()
    for m in (m_owner, m_a, m_b):
        db.refresh(m)

    return {"tenant": t, "owner": m_owner, "member_a": m_a, "member_b": m_b}
