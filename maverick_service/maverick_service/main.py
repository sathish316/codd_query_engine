"""Main FastAPI application for Maverick Service."""

from fastapi import FastAPI
from maverick_service.api.controllers import (
    hello_controller,
    metrics_controller,
    logs_controller,
)

# Create FastAPI app
app = FastAPI(
    title="Maverick Service",
    description="FastAPI REST service for Maverick observability operations",
    version="0.1.0",
)

# Include routers
app.include_router(hello_controller.router, prefix="/api", tags=["hello"])
app.include_router(metrics_controller.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(logs_controller.router, prefix="/api/logs", tags=["logs"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Maverick Service",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
