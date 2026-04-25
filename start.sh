#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo ".env file not found."
  echo "Create the .env file with your key:"
  echo "  echo 'ANTHROPIC_API_KEY=your_key_here' > .env"
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "========================================"
echo "  KickPlus starting at:"
echo "  http://localhost:8000"
echo "========================================"
echo ""

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
