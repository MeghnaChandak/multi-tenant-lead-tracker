import re

from sqlalchemy.orm import Session

from app.models.tenant import Tenant


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "tenant"


def create_tenant(db: Session, name: str) -> Tenant:
    base_slug = slugify(name)
    slug = base_slug
    suffix = 1
    # Ensure uniqueness without relying on a DB round-trip race —
    # acceptable for this project's scale; a high-concurrency version
    # would catch the IntegrityError on insert instead.
    while db.query(Tenant).filter(Tenant.slug == slug).first() is not None:
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    tenant = Tenant(name=name, slug=slug, subscription_status="inactive")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def get_tenant(db: Session, tenant_id: int) -> Tenant | None:
    return (
        db.query(Tenant)
        .filter(Tenant.id == tenant_id, Tenant.is_deleted == False)
        .first()
    )
