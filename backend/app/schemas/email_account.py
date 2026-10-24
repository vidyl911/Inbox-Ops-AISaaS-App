from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailAccountCreate(BaseModel):
    organization_id: int = Field(gt=0)
    provider: str = Field(min_length=1, max_length=30)
    email_address: EmailStr
    display_name: str | None = Field(default=None, max_length=150)


class EmailAccountRead(BaseModel):
    id: int
    organization_id: int
    provider: str
    email_address: str
    display_name: str | None
    status: str
    connected_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
