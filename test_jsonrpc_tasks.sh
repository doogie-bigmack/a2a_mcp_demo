#!/bin/bash
# Test A2A JSON-RPC endpoints for tasks_send, tasks_get, and tasks_cancel using curl
# Usage: bash test_jsonrpc_tasks.sh

set -e
API_URL="http://localhost:8080/"
TOKEN="ay5cJzvq0ERBJ3K3b_rGTaeZuykbWqGcvU23KMzDRRk"  # Synced with .env A2A_BEARER_TOKEN

# 1. Create a new task (tasks_send)
echo "\n--- Creating a new task (tasks_send) ---"
SEND_RESP=$(curl -s -X POST "$API_URL" \
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
  TASK_ID=$(echo "$SEND_RESP" | jq -r '.result.task.id // empty')
else
  TASK_ID=$(echo "$SEND_RESP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', {}).get('task', {}).get('id', ''))")
fi
if [ -z "$TASK_ID" ]; then
  echo "ERROR: Could not extract task ID from SEND_RESP. Full response: $SEND_RESP" >&2
  exit 1
fi

# 2. Get task status (tasks_get)
echo "\n--- Getting task status (tasks_get) ---"
GET_RESP=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tasks_get",
    "params": {"id": "'$TASK_ID'", "historyLength": 0}
  }')
echo "$GET_RESP"

# 3. Cancel the task (tasks_cancel)
echo "\n--- Cancelling the task (tasks_cancel) ---"
CANCEL_RESP=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tasks_cancel",
    "params": {"id": "'$TASK_ID'"}
  }')
echo "$CANCEL_RESP"

# 4. Try to cancel again (should get -32002 error)
echo "\n--- Cancelling again (should fail with -32002) ---"
CANCEL_AGAIN_RESP=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tasks_cancel",
    "params": {"id": "'$TASK_ID'"}
  }')
echo "$CANCEL_AGAIN_RESP"

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
