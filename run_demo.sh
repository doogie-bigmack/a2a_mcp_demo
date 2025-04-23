#!/bin/bash

set -e
# Print .env file contents if accessible
if [ -f .env ]; then
  echo "\n===== .env file contents ====="
  cat .env
  echo "===== End .env file contents =====\n"
else
  echo ".env file not found or not readable."
fi
# Print all environment variables relevant to the test
echo "\n===== Environment Variables ====="
env | grep -E 'A2A|BRAVE|LOGFIRE|OPENAI|PYTHON_ENV|SERVER_URL|TOKEN|KEY|URL'
echo "===== End Environment Variables =====\n"
set -e

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Start Brave MCP server in the background if not already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null; then
  echo "Brave MCP server already running on port 3000."
else
  echo "Starting Brave MCP server on port 3000..."
  nohup npx -y @modelcontextprotocol/server-brave-search > brave_mcp.log 2>&1 &
  sleep 5
  echo "Brave MCP server started. Logs: brave_mcp.log"
fi

# Build and start Docker Compose stack
echo "Building and starting Docker containers..."
docker compose up --build -d

# Optionally, run a test if a sample Dockerfile exists
if [ -f shared/sample.Dockerfile ]; then
  echo "Submitting sample.Dockerfile for hardening..."
  docker compose run client python main.py --dockerfile /app/shared/sample.Dockerfile
else
  echo "No sample.Dockerfile found in shared/. Skipping test submission."
fi

echo "Demo is up! MCP server logs: brave_mcp.log"
