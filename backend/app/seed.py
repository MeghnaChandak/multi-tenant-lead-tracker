"""Run once after `alembic upgrade head`:

    python -m app.seed

Populates the lead_statuses lookup table. Safe to re-run — skips codes
that already exist.
"""

from app.database import SessionLocal
from app.models.lead_status import SEED_STATUSES, LeadStatus


def run():
    db = SessionLocal()
    try:
        existing_codes = {row.code for row in db.query(LeadStatus.code).all()}
        added = 0
        for status in SEED_STATUSES:
            if status["code"] not in existing_codes:
                db.add(LeadStatus(**status))
                added += 1
        db.commit()
        print(f"Seeded {added} lead statuses ({len(existing_codes)} already present).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
