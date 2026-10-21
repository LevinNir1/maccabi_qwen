# Single container: Ollama (serves the Qwen model locally) + FastAPI (the coding API).
# Internet is needed only while building; the built image runs fully offline.

# Start from the official Ollama image (pinned version): provides the `ollama` server and model runtime
FROM ollama/ollama:0.32.15

# Install Python 3 (and venv support) to run the API; delete apt's package lists to keep the image smaller
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Which model to bake in; override at build time with MODEL=... (docker-compose.yml passes it through)
ARG MODEL=qwen3:4b-instruct-2507-q8_0
# Make the same settings available when the container runs:
#   MODEL       - the model the API asks Ollama for (always the one downloaded below)
#   OLLAMA_URL  - where the API finds Ollama (inside this container)
#   OLLAMA_KEEP_ALIVE - keep the model loaded in memory for 60 min between requests
ENV MODEL=${MODEL} OLLAMA_URL=http://127.0.0.1:11434 OLLAMA_KEEP_ALIVE=60m

# Download the model weights into the image (the only step that uses the internet):
# start a temporary Ollama server in the background, wait until it answers, then pull the model
RUN ollama serve > /tmp/ollama-build.log 2>&1 & \
    until ollama list > /dev/null 2>&1; do sleep 1; done; \
    ollama pull ${MODEL}

# All following paths are relative to /app
WORKDIR /app
# Copy the dependency list first, so the pip layer is cached when only the code changes
COPY requirements.txt .
# Create an isolated Python environment and install the pinned dependencies (requests, fastapi, uvicorn)
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt
# Copy the application code
COPY src ./src
# Copy the official ICD-10-CM FY2027 tabular XML (the code catalog the pipeline navigates)
COPY data/icd10cm-tabular-2027.xml ./data/

# Document that the API listens on port 8000 (docker-compose.yml maps it to the host)
EXPOSE 8000
# Copy the startup script: starts Ollama, waits for it, then starts the API
COPY docker/entrypoint.sh /entrypoint.sh
# Run the startup script when the container starts (replaces the base image's default `ollama` entrypoint)
ENTRYPOINT ["/entrypoint.sh"]
