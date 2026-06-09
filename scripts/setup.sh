#!/bin/bash
# OmClaw Development Setup Script
# Run once after cloning: ./scripts/setup.sh

set -e
echo "🦾 Setting up OmClaw..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required="3.12"
if [ "$(printf '%s\n' "$required" "$python_version" | sort -V | head -n1)" != "$required" ]; then
  echo "❌ Python 3.12+ required. Found: $python_version"
  exit 1
fi
echo "✅ Python $python_version"

# Check Ollama
if ! command -v ollama &> /dev/null; then
  echo "⚠️  Ollama not found. Install from https://ollama.com/download"
else
  echo "✅ Ollama installed"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
  echo "⚠️  Docker not found. Install from https://docs.docker.com/get-docker/"
else
  echo "✅ Docker installed"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -e ".[dev]"

# Copy .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "📋 Created .env from .env.example — edit it and set your config!"
fi

# Create workspace
mkdir -p workspace
echo "✅ Workspace directory created"

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium || echo "⚠️  Playwright install failed — browser tools won't work until fixed"

# Pull Ollama model
echo "🤖 Pulling Ollama model (qwen2.5-coder:14b)..."
ollama pull qwen2.5-coder:14b || echo "⚠️  Model pull failed — ensure Ollama is running: ollama serve"

echo ""
echo "🎉 OmClaw setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env if needed"
echo "  2. Build sandbox: docker build -t omclaw-sandbox:latest -f docker/Dockerfile.sandbox ."
echo "  3. Start API: uvicorn backend.api.main:app --reload"
echo "  4. Open: http://localhost:8000/docs"
