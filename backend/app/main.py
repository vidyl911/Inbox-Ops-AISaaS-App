from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/")
def root():
    return {
        "message": "Welcome to the InboxOps API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "InboxOps API",
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)
