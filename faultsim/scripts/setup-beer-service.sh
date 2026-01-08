#!/bin/bash
set -e

echo "Starting beer service with Docker Compose..."

# Navigate to the beer service directory
BEER_SERVICE_PATH="${BEER_SERVICE_PATH:-sandbox/beer-service-sandbox}"

if [ ! -d "$BEER_SERVICE_PATH" ]; then
    echo "Error: Beer service path not found: $BEER_SERVICE_PATH"
    exit 1
fi

cd "$BEER_SERVICE_PATH"

# Start services with docker-compose
docker-compose up -d

echo "Waiting for services to be healthy..."

# Wait for beer-service to be healthy
MAX_WAIT=120
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:5001/health > /dev/null 2>&1; then
        echo "Beer service is healthy!"
        exit 0
    fi
    echo "Waiting for beer service... ($ELAPSED/$MAX_WAIT seconds)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo "Error: Beer service did not become healthy within $MAX_WAIT seconds"
exit 1
