from typing import Literal

from pydantic import BaseModel

# ---- Server -> client events ----

class LeadChangedEvent(BaseModel):
    type: Literal["lead_changed"] = "lead_changed"
    lead_id: int
    status_code: str
    assigned_to: int | None
    changed_by: int


class PipelineUpdatedEvent(BaseModel):
    type: Literal["pipeline_updated"] = "pipeline_updated"
    by_status: dict[str, int]
    total: int


class PresenceEvent(BaseModel):
    type: Literal["presence"] = "presence"
    lead_id: int
    viewers: list[int]  # user_ids currently viewing this lead


class ConflictWarningEvent(BaseModel):
    type: Literal["conflict_warning"] = "conflict_warning"
    lead_id: int
    message: str = "This lead was just changed by someone else. Reload before editing."


# ---- Client -> server messages ----

class ViewLeadMessage(BaseModel):
    type: Literal["view_lead"]
    lead_id: int


class LeaveLeadMessage(BaseModel):
    type: Literal["leave_lead"]
    lead_id: int
