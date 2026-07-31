#!/usr/bin/env bash
# DeceptiScan Build Script

set -e

echo "=== DeceptiScan Production Build ==="

echo "1. Building React Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "2. Validating Backend Dependencies..."
cd backend
python -m pip install -r requirements.txt --quiet
cd ..

echo "3. Building Docker Stack..."
docker compose build

echo "=== Build Complete ==="
