"""Main FastAPI application for Codd Service."""

import logging
import os
import sys

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Avoid HuggingFace tokenizers fork warnings in uvicorn workers.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from fastapi import FastAPI
from codd_lib.config import CoddConfig
from codd_service.api.controllers import (
    hello_controller,
    metrics_controller,
    logs_controller,
)

# Conditionally enable logfire based on config
_config = CoddConfig.from_config_file()
if _config.debug.logfire_enabled:
    import logfire
    logfire.configure()
    logfire.instrument_pydantic_ai()

# Create FastAPI app
app = FastAPI(
    title="Codd Service",
    description="FastAPI REST service for Codd query engine",
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
        "message": "Welcome to Codd Service",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the Codd Service with uvicorn."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=2840)
