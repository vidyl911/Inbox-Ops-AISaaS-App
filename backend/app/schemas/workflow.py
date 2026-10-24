from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowCreate(BaseModel):
    organization_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=150)
    trigger_type: str = Field(min_length=1, max_length=50)
    configuration: dict[str, Any] = Field(default_factory=dict)


class WorkflowRead(BaseModel):
    id: int
    organization_id: int
    name: str
    trigger_type: str
    configuration: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    trigger_type: str | None = Field(default=None, min_length=1, max_length=50)
    configuration: dict[str, Any] | None = None
    is_active: bool | None = None
