from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkflowExecutionCreate(BaseModel):
    trigger_source: Literal["manual", "scheduled", "event"] = "manual"


class WorkflowExecutionRead(BaseModel):
    id: int
    workflow_id: int
    status: str
    trigger_source: str
    started_at: datetime | None
    finished_at: datetime | None
    result: dict[str, Any] | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
