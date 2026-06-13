#!/usr/bin/env bash
# One-command local launch for the Capture Inbox -> Obsidian Sorter prototype.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q -r requirements.txt

export VAULT_DIR="${VAULT_DIR:-vault}"
export SORTER_DB="${SORTER_DB:-sorter.db}"
# CLASSIFIER=rules (default, no API key) | llm | ensemble
export CLASSIFIER="${CLASSIFIER:-rules}"

echo "Starting on http://127.0.0.1:8000  (classifier=$CLASSIFIER)"
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
