from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.schemas.workflow_execution import (
    WorkflowExecutionCreate,
    WorkflowExecutionRead,
)

router = APIRouter(tags=["Workflow Executions"])


@router.post(
    "/workflows/{workflow_id}/executions",
    response_model=WorkflowExecutionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_execution(
    workflow_id: int,
    payload: WorkflowExecutionCreate,
    db: Session = Depends(get_db),
):
    workflow = db.get(Workflow, workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    if not workflow.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot create an execution for an inactive workflow.",
        )

    execution = WorkflowExecution(
        workflow_id=workflow_id,
        trigger_source=payload.trigger_source,
        status="queued",
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    return execution


@router.get(
    "/workflows/{workflow_id}/executions",
    response_model=list[WorkflowExecutionRead],
)
def list_executions(
    workflow_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    workflow = db.get(Workflow, workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    statement = (
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.created_at.desc())
        .limit(limit)
    )

    return db.scalars(statement).all()


@router.get(
    "/executions/{execution_id}",
    response_model=WorkflowExecutionRead,
)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
):
    execution = db.get(WorkflowExecution, execution_id)

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found.",
        )

    return execution


@router.post(
    "/executions/{execution_id}/run",
    response_model=WorkflowExecutionRead,
)
def run_execution(
    execution_id: int,
    db: Session = Depends(get_db),
):
    execution = db.get(WorkflowExecution, execution_id)

    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow execution not found.",
        )

    if execution.status != "queued":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Execution cannot run from status '{execution.status}'.",
        )

    workflow = db.get(Workflow, execution.workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated workflow not found.",
        )

    execution.status = "running"
    execution.started_at = datetime.now(timezone.utc)

    # Prototype only: simulate a successful workflow run.
    execution.result = {
        "message": "Simulated workflow execution completed.",
        "workflow_name": workflow.name,
        "actions_configured": workflow.configuration,
    }
    execution.status = "succeeded"
    execution.error_message = None
    execution.finished_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(execution)

    return execution
