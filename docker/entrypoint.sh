#!/bin/sh
# Container startup: run the local Ollama server, wait until it is ready, then start the API.
# Exit immediately if any command fails
set -e
# Start Ollama in the background (it serves the model baked into the image); log to /tmp/ollama.log
ollama serve > /tmp/ollama.log 2>&1 &
# Wait until Ollama answers requests
until ollama list > /dev/null 2>&1; do sleep 1; done
# Replace this shell with the API server, listening on all interfaces, port 8000
exec /venv/bin/uvicorn src.api:app --host 0.0.0.0 --port 8000
