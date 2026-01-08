#!/bin/bash

BASE_URL="${1:-http://localhost:5001}"
RPS="${2:-10}"

echo "Generating traffic to $BASE_URL at $RPS requests/second..."

# Endpoints to hit
ENDPOINTS=(
    "/beers"
    "/health"
    "/ready"
    "/beers/1"
    "/beers/2"
)

# Calculate delay between requests
DELAY=$(echo "scale=3; 1.0 / $RPS" | bc)

# Run indefinitely until killed
while true; do
    for endpoint in "${ENDPOINTS[@]}"; do
        curl -sf "${BASE_URL}${endpoint}" > /dev/null 2>&1 || true
        sleep "$DELAY"
    done
done
