"""Hello World controller with GET and POST endpoints."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()


class HelloRequest(BaseModel):
    """Request model for POST endpoint."""

    name: str


class HelloResponse(BaseModel):
    """Response model for hello endpoints."""

    message: str
    name: str


@router.get("/hello", response_model=HelloResponse)
async def hello_get(name: str = Query(..., description="Name for greeting")):
    """
    GET endpoint that takes a query parameter for name.

    Args:
        name: Name to greet (query parameter)

    Returns:
        HelloResponse with greeting message

    Example:
        GET /api/hello?name=World
        Response: {"message": "Hello, World!", "name": "World"}
    """
    return HelloResponse(message=f"Hello, {name}!", name=name)


@router.post("/hello", response_model=HelloResponse)
async def hello_post(request: HelloRequest):
    """
    POST endpoint that takes a payload parameter for name.

    Args:
        request: HelloRequest with name field

    Returns:
        HelloResponse with greeting message

    Example:
        POST /api/hello
        Body: {"name": "World"}
        Response: {"message": "Hello, World!", "name": "World"}
    """
    return HelloResponse(message=f"Hello, {request.name}!", name=request.name)
