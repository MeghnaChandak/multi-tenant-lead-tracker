from app.models.lead import Lead
from app.ws.manager import manager


def broadcast_lead_changed(lead: Lead, *, changed_by: int):
    manager.notify_lead_changed(
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        status_code=lead.status.code,
        assigned_to=lead.assigned_to,
        changed_by=changed_by,
    )


def broadcast_pipeline_updated(*, tenant_id: int, summary: dict):
    manager.notify_pipeline_updated(tenant_id=tenant_id, by_status=summary["by_status"], total=summary["total"])


def broadcast_conflict(*, tenant_id: int, lead_id: int):
    manager.notify_conflict(tenant_id=tenant_id, lead_id=lead_id)
