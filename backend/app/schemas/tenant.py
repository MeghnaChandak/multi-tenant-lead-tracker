from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


class CreateTenantRequest(BaseModel):
    name: str

    model_config = ConfigDict(extra="forbid")


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    subscription_status: str

    model_config = ConfigDict(from_attributes=True)


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: Literal["admin", "member"]  # can't invite someone directly as owner

    model_config = ConfigDict(extra="forbid")


class MembershipResponse(BaseModel):
    id: int
    user_id: int
    tenant_id: int
    role: str

    model_config = ConfigDict(from_attributes=True)
