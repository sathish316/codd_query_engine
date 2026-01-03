# Maverick Service

FastAPI REST service for Maverick observability operations.

## Features

- FastAPI-based REST API
- Hello World endpoints (GET and POST)
- Auto-generated OpenAPI documentation
- Health check endpoint

## Installation

```bash
# Install in the workspace
uv sync
```

## Running the Service

```bash
# Run with uvicorn
uv run uvicorn maverick_service.main:app --reload

# Or specify host and port
uv run uvicorn maverick_service.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Root Endpoints

**GET /**
- Description: Root endpoint with service information
- Response:
  ```json
  {
    "message": "Welcome to Maverick Service",
    "version": "0.1.0",
    "docs": "/docs"
  }
  ```

**GET /health**
- Description: Health check endpoint
- Response:
  ```json
  {
    "status": "healthy"
  }
  ```

### Hello World Endpoints

**GET /api/hello**
- Description: Hello world endpoint with query parameter
- Parameters:
  - `name` (query, required): Name for greeting
- Response:
  ```json
  {
    "message": "Hello, World!",
    "name": "World"
  }
  ```
- Example:
  ```bash
  curl "http://localhost:8000/api/hello?name=World"
  ```

**POST /api/hello**
- Description: Hello world endpoint with payload
- Request Body:
  ```json
  {
    "name": "World"
  }
  ```
- Response:
  ```json
  {
    "message": "Hello, World!",
    "name": "World"
  }
  ```
- Example:
  ```bash
  curl -X POST "http://localhost:8000/api/hello" \
    -H "Content-Type: application/json" \
    -d '{"name": "World"}'
  ```

## Testing

```bash
# Run all tests
uv run pytest maverick_service/tests -v

# Run with coverage
uv run pytest maverick_service/tests --cov=maverick_service
```

## Development

The service is organized with:
- `maverick_service/main.py`: Main FastAPI application
- `maverick_service/api/controllers/`: API endpoint controllers
- `maverick_service/tests/`: Test suite

## API Documentation

Once the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
