#!/bin/bash
# Test A2A JSON-RPC endpoints for tasks_send, tasks_get, and tasks_cancel using curl
# Usage: bash test_jsonrpc_tasks.sh

#!/bin/bash
set -euo pipefail

# Source .env and export variables if it exists
if [ -f .env ]; then
  echo "\n===== .env file contents (including secrets) ====="
  cat .env
  echo "===== End .env file contents =====\n"
  set -o allexport
  source .env
  set +o allexport
else
  echo ".env file not found or not readable."
fi

# Print all environment variables relevant to the test (including secrets)
echo "\n===== Environment Variables (including secrets) ====="
env | grep -E 'A2A|BRAVE|LOGFIRE|OPENAI|PYTHON_ENV|SERVER_URL|TOKEN|KEY|URL'
echo "===== End Environment Variables =====\n"

echo "PYTHONPATH: ${PYTHONPATH:-}"
pwd
ls -l
docker compose ps
docker compose logs server

# Print all environment variables relevant to the test (including secrets)
echo "\n===== Environment Variables (including secrets) ====="
env | grep -E 'A2A|BRAVE|LOGFIRE|OPENAI|PYTHON_ENV|SERVER_URL|TOKEN|KEY|URL'
echo "===== End Environment Variables =====\n"
# Robust TOKEN assignment
if [ -z "${TOKEN:-}" ]; then
  if [ -n "${A2A_BEARER_TOKEN:-}" ]; then
    TOKEN="${A2A_BEARER_TOKEN}"
    echo "TOKEN set from A2A_BEARER_TOKEN: $TOKEN"
  else
    TOKEN="test-token"
    echo "TOKEN not set; using fallback: $TOKEN"
  fi
fi
API_URL="http://localhost:8080/"

# 1. Create a new task (tasks_send)
echo "\n--- Creating a new task (tasks_send) ---"
echo "Request: POST $API_URL"
echo "Headers: Authorization: Bearer ${TOKEN:-}, Content-Type: application/json"
echo "Headers: Authorization: Bearer $TOKEN, Content-Type: application/json"
echo "Payload: {\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tasks_send\", \"params\": {\"raw_text\": \"FROM python:3.12-slim\\nCMD [\\\"python\\\", \\\"app.py\\\"]\"}}"
SEND_RESP=$(curl -v -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tasks_send",
    "params": {"raw_text": "FROM python:3.12-slim\nCMD [\"python\", \"app.py\"]"}
  }')
echo "Raw SEND_RESP: $SEND_RESP"
if command -v jq >/dev/null 2>&1; then
  TASK_ID=$(echo "$SEND_RESP" | jq -r '.result.result.task.id // empty')
else
  TASK_ID=$(echo "$SEND_RESP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', {}).get('result', {}).get('task', {}).get('id', ''))")
fi
echo "Extracted TASK_ID: $TASK_ID"
if [ -z "$TASK_ID" ]; then
  echo "ERROR: Could not extract task ID from SEND_RESP. Full response: $SEND_RESP" >&2
  exit 1
fi

# 2. Get task status (tasks_get)
echo "\n--- Getting task status (tasks_get) ---"
echo "Request: POST $API_URL"
echo "Headers: Authorization: Bearer $TOKEN, Content-Type: application/json"
echo "Payload: {\"jsonrpc\": \"2.0\", \"id\": 2, \"method\": \"tasks_get\", \"params\": {\"id\": \"$TASK_ID\", \"historyLength\": 0}}"
GET_RESP=$(curl -v -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tasks_get",
    "params": {"id": "'$TASK_ID'", "historyLength": 0}
  }')
echo "Raw GET_RESP: $GET_RESP"

# 3. Cancel the task (tasks_cancel)
echo "\n--- Cancelling the task (tasks_cancel) ---"
echo "Request: POST $API_URL"
echo "Headers: Authorization: Bearer $TOKEN, Content-Type: application/json"
echo "Payload: {\"jsonrpc\": \"2.0\", \"id\": 3, \"method\": \"tasks_cancel\", \"params\": {\"id\": \"$TASK_ID\"}}"
CANCEL_RESP=$(curl -v -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tasks_cancel",
    "params": {"id": "'$TASK_ID'"}
  }')
echo "Raw CANCEL_RESP: $CANCEL_RESP"

# 4. Try to cancel again (should get -32002 error)
echo "\n--- Cancelling again (should fail with -32002) ---"
echo "Request: POST $API_URL"
echo "Headers: Authorization: Bearer $TOKEN, Content-Type: application/json"
echo "Payload: {\"jsonrpc\": \"2.0\", \"id\": 4, \"method\": \"tasks_cancel\", \"params\": {\"id\": \"$TASK_ID\"}}"
CANCEL_AGAIN_RESP=$(curl -v -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tasks_cancel",
    "params": {"id": "'$TASK_ID'"}
  }')
echo "Raw CANCEL_AGAIN_RESP: $CANCEL_AGAIN_RESP"

# 5. Get status for unknown task (should get -32001 error)
echo "\n--- Getting status for unknown task (should fail with -32001) ---"
GET_UNKNOWN_RESP=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "tasks_get",
    "params": {"id": "doesnotexist", "historyLength": 0}
  }')
echo "$GET_UNKNOWN_RESP"

echo "\nAll tests completed."
