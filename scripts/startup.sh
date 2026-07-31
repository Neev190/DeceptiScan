#!/usr/bin/env bash
# DeceptiScan Startup Script

set -e

echo "=== DeceptiScan Service Startup ==="

echo "1. Starting Docker Containers..."
docker compose up -d postgres redis

echo "2. Running Database Migrations..."
docker compose exec backend flask db upgrade || true

echo "3. Launching Full Application Stack..."
docker compose up -d

echo "=== Services Running at http://localhost ==="
