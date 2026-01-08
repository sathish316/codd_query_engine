#!/bin/bash
set -e

echo "Stopping Redis container to simulate cache failure..."

# Find and stop Redis container in the beer service compose project
REDIS_CONTAINER=$(docker ps --filter "name=redis" --format "{{.Names}}" | grep -i beer || true)

if [ -z "$REDIS_CONTAINER" ]; then
    echo "Warning: No Redis container found. Looking for any redis container..."
    REDIS_CONTAINER=$(docker ps --filter "name=redis" --format "{{.Names}}" | head -n1)
fi

if [ -z "$REDIS_CONTAINER" ]; then
    echo "Error: Could not find Redis container"
    exit 1
fi

echo "Stopping container: $REDIS_CONTAINER"
docker stop "$REDIS_CONTAINER"

echo "Redis container stopped successfully"
