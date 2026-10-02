from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

VALID_STATUS_CODES = {"new", "contacted", "qualified", "proposal_sent", "won", "lost"}


class CreateLeadRequest(BaseModel):
    name: str
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    source: str | None = None
    next_follow_up_date: date | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be blank")
        return v.strip()


class UpdateLeadRequest(BaseModel):
    # version is required — this is what makes the update optimistic-locked
    version: int

    status_code: str | None = None
    assigned_to: int | None = None
    next_follow_up_date: date | None = None
    name: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    source: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("status_code")
    @classmethod
    def status_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_STATUS_CODES:
            raise ValueError(f"status_code must be one of {sorted(VALID_STATUS_CODES)}")
        return v


class AddActivityRequest(BaseModel):
    note: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("note")
    @classmethod
    def note_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("note cannot be blank")
        return v.strip()


class LeadResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    company: str | None
    phone: str | None
    email: str | None
    source: str | None
    status_code: str
    assigned_to: int | None
    next_follow_up_date: date | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DuplicateWarning(BaseModel):
    lead_id: int
    name: str
    company: str | None
    similarity: float
    created_at: datetime


class CreateLeadResponse(BaseModel):
    lead: LeadResponse
    possible_duplicates: list[DuplicateWarning] = []


class ActivityResponse(BaseModel):
    id: int
    lead_id: int
    user_id: int
    note: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineSummaryResponse(BaseModel):
    by_status: dict[str, int]
    total: int
    won: int
    lost: int
    conversion_rate: float
