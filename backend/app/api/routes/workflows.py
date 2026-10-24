from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.organization import Organization
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowRead, WorkflowUpdate

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post(
    "",
    response_model=WorkflowRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
):
    organization = db.get(Organization, payload.organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    workflow = Workflow(
        organization_id=payload.organization_id,
        name=payload.name,
        trigger_type=payload.trigger_type,
        configuration=payload.configuration,
    )

    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    return workflow


@router.get("", response_model=list[WorkflowRead])
def list_workflows(
    organization_id: int,
    db: Session = Depends(get_db),
):
    organization = db.get(Organization, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    statement = (
        select(Workflow)
        .where(Workflow.organization_id == organization_id)
        .order_by(Workflow.id)
    )
    return db.scalars(statement).all()


@router.get("/{workflow_id}", response_model=WorkflowRead)
def get_workflow(
    workflow_id: int,
    db: Session = Depends(get_db),
):
    workflow = db.get(Workflow, workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    return workflow


@router.patch("/{workflow_id}", response_model=WorkflowRead)
def update_workflow(
    workflow_id: int,
    payload: WorkflowUpdate,
    db: Session = Depends(get_db),
):
    workflow = db.get(Workflow, workflow_id)

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )
        if isinstance(value, str) and not value.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be blank.",
            )
        setattr(workflow, field, value)

    db.commit()
    db.refresh(workflow)

    return workflow
