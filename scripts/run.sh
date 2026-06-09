#!/bin/bash
# Quick-start OmClaw backend
set -e
echo "🚀 Starting OmClaw API..."
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
