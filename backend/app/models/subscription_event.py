from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class SubscriptionEvent(Base):
    __tablename__ = "subscription_events"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    stripe_event_id = Column(String(255), nullable=False, unique=True)
    type = Column(String(100), nullable=False)
    # JSONB on Postgres (queryable/indexable); falls back to generic JSON
    # on other dialects (e.g. SQLite in tests) — same data, portable DDL.
    payload_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    # No is_deleted / updated_by — this is a machine-only, immutable log,
    # never edited by a person.
