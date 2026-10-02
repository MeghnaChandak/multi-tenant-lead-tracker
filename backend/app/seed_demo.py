"""Run once after `alembic upgrade head` and `python -m app.seed`:

    python -m app.seed_demo

Creates a demo workspace with subscription_status='active' (important —
otherwise recruiters/interviewers hit a 402 the moment they try to view
leads, since real tenants only go active via a real Stripe checkout).
Safe to re-run — skips if the demo tenant already exists.

Demo login printed at the end.
"""

from datetime import date, timedelta

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.lead import Lead
from app.models.lead_status import LeadStatus
from app.models.membership import Membership
from app.models.tenant import Tenant
from app.models.user import User

DEMO_PASSWORD = "DemoPass123!"


def run():
    db = SessionLocal()
    try:
        existing = db.query(Tenant).filter(Tenant.slug == "demo-workspace").first()
        if existing:
            print("Demo tenant already exists — skipping.")
            print(f"Demo login: owner@demo.com / {DEMO_PASSWORD}")
            return

        # Hash passwords BEFORE creating anything in the DB — if bcrypt/passlib
        # fails, we fail before any partial state is written, so a retry
        # never finds a half-seeded tenant.
        owner_hash = hash_password(DEMO_PASSWORD)
        admin_hash = hash_password(DEMO_PASSWORD)
        member_hash = hash_password(DEMO_PASSWORD)

        tenant = Tenant(
            name="Demo Workspace",
            slug="demo-workspace",
            subscription_status="active",  # bypasses the real Stripe gate for the public demo
        )
        db.add(tenant)
        db.flush()  # assigns tenant.id without committing yet

        owner = User(email="owner@demo.com", hashed_password=owner_hash)
        admin = User(email="admin@demo.com", hashed_password=admin_hash)
        member = User(email="member@demo.com", hashed_password=member_hash)
        db.add_all([owner, admin, member])
        db.flush()  # assigns user ids without committing yet

        db.add_all([
            Membership(user_id=owner.id, tenant_id=tenant.id, role="owner"),
            Membership(user_id=admin.id, tenant_id=tenant.id, role="admin"),
            Membership(user_id=member.id, tenant_id=tenant.id, role="member"),
        ])
        db.commit()  # everything above commits together, or not at all

        statuses = {s.code: s.id for s in db.query(LeadStatus).all()}
        if not statuses:
            print("No lead_statuses found — run `python -m app.seed` first.")
            return

        today = date.today()
        sample_leads = [
            dict(name="Rohan Mehta", company="Bluewave Textiles", phone="9800000001",
                 status_id=statuses["proposal_sent"], assigned_to=member.id,
                 next_follow_up_date=today, source="referral"),
            dict(name="Neha Kulkarni", company="Kul Foods Pvt Ltd", phone="9800000002",
                 status_id=statuses["contacted"], assigned_to=member.id,
                 next_follow_up_date=today, source="website"),
            dict(name="Priya Nair", company="Nair Interiors", phone="9800000003",
                 status_id=statuses["qualified"], assigned_to=admin.id,
                 next_follow_up_date=today + timedelta(days=2), source="cold_call"),
            dict(name="Vikram Shah", company="Shah Electricals", phone="9800000004",
                 status_id=statuses["won"], assigned_to=admin.id,
                 next_follow_up_date=None, source="referral"),
        ]
        for data in sample_leads:
            db.add(Lead(tenant_id=tenant.id, created_by=owner.id, version=1, **data))
        db.commit()

        print("Demo workspace seeded.")
        print(f"Demo login: owner@demo.com / {DEMO_PASSWORD}  (also admin@demo.com, member@demo.com)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
