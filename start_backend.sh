#!/bin/bash
# ORION — Quick start backend
set -e

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  Created .env from template."
  echo "   Please edit backend/.env and set DATABASE_URL and SECRET_KEY before continuing."
  exit 1
fi

echo "Creating database tables..."
python -c "from database import engine, Base; import models; Base.metadata.create_all(engine); print('Tables ready.')"

echo "Starting ORION backend on http://localhost:8000 ..."
uvicorn main:app --reload --port 8000
