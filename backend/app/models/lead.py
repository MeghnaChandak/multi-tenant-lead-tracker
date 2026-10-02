from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("idx_leads_tenant", "tenant_id", postgresql_where=(Column("is_deleted") == False)),
        Index(
            "idx_leads_assigned", "tenant_id", "assigned_to",
            postgresql_where=(Column("is_deleted") == False),
        ),
        Index(
            "idx_leads_follow_up", "tenant_id", "next_follow_up_date",
            postgresql_where=(Column("is_deleted") == False),
        ),
        Index("idx_leads_name_trgm", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
        Index(
            "idx_leads_company_trgm", "company", postgresql_using="gin",
            postgresql_ops={"company": "gin_trgm_ops"},
        ),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    source = Column(String(50), nullable=True)

    status_id = Column(Integer, ForeignKey("lead_statuses.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    next_follow_up_date = Column(Date, nullable=True)

    # Optimistic locking: every update must supply the version it last read.
    # A mismatch means someone else changed the row first.
    version = Column(Integer, nullable=False, default=1)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)

    status = relationship("LeadStatus")
