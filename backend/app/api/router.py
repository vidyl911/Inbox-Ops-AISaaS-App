from fastapi import APIRouter

from app.api.routes import (
    email_accounts,
    health,
    organizations,
    workflow_executions,
    workflows,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(organizations.router)
api_router.include_router(email_accounts.router)
api_router.include_router(workflows.router)
api_router.include_router(workflow_executions.router)
