from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
        CheckConstraint("role in ('owner', 'admin', 'member')", name="ck_membership_role"),
        # Enforces "exactly one owner per tenant" as a DB-level invariant,
        # not just an application-layer rule.
        Index(
            "one_owner_per_tenant",
            "tenant_id",
            unique=True,
            postgresql_where=(Column("role") == "owner") & (Column("is_deleted") == False),
            sqlite_where=(Column("role") == "owner") & (Column("is_deleted") == False),
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    role = Column(String(20), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="memberships")
    tenant = relationship("Tenant", back_populates="memberships")
