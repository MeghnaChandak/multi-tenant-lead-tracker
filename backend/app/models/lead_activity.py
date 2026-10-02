from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func

from app.database import Base


class LeadActivity(Base):
    __tablename__ = "lead_activity"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Append-only: no updated_at / is_deleted. Activity notes are a
    # historical record, not an editable field.
