from sqlalchemy import Column, Integer, String

from app.database import Base


class LeadStatus(Base):
    __tablename__ = "lead_statuses"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), nullable=False, unique=True)
    label = Column(String(50), nullable=False)
    sort_order = Column(Integer, nullable=False)


# Seed values — used by both the seed script and anywhere code needs the
# canonical set without hitting the DB (e.g. validating a status code).
SEED_STATUSES = [
    {"code": "new", "label": "New", "sort_order": 1},
    {"code": "contacted", "label": "Contacted", "sort_order": 2},
    {"code": "qualified", "label": "Qualified", "sort_order": 3},
    {"code": "proposal_sent", "label": "Proposal sent", "sort_order": 4},
    {"code": "won", "label": "Won", "sort_order": 5},
    {"code": "lost", "label": "Lost", "sort_order": 6},
]

CLOSED_STATUS_CODES = {"won", "lost"}
