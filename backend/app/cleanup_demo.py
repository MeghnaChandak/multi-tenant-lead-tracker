"""One-off: removes the demo tenant (and anything referencing it) so
`python -m app.seed_demo` can recreate it cleanly. Safe to run even if
the demo tenant doesn't exist yet.

    python -m app.cleanup_demo
"""

from app.database import SessionLocal
from app.models.tenant import Tenant
from app.models.membership import Membership
from app.models.lead import Lead
from app.models.lead_activity import LeadActivity
from app.models import tenant, user, membership, lead_status, lead, lead_activity  # noqa: F401 — ensures all models are registered before any query runs


def run():
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == "demo-workspace").first()
        if tenant is None:
            print("No demo tenant found — nothing to clean up.")
            return

        lead_ids = [l.id for l in db.query(Lead).filter(Lead.tenant_id == tenant.id).all()]
        if lead_ids:
            db.query(LeadActivity).filter(LeadActivity.lead_id.in_(lead_ids)).delete(synchronize_session=False)
            db.query(Lead).filter(Lead.tenant_id == tenant.id).delete(synchronize_session=False)
        db.query(Membership).filter(Membership.tenant_id == tenant.id).delete(synchronize_session=False)
        db.delete(tenant)
        db.commit()
        print(f"Removed incomplete demo tenant (id={tenant.id}) and its related rows.")
    finally:
        db.close()


if __name__ == "__main__":
    run()