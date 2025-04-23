#!/bin/bash

set -e
# Print .env file contents and export all variables
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
# Set TOKEN if not already set
if [ -z "$TOKEN" ] && [ ! -z "$A2A_BEARER_TOKEN" ]; then
  # Robust TOKEN assignment
if [ -z "${TOKEN:-}" ]; then
  if [ -n "${A2A_BEARER_TOKEN:-}" ]; then
    TOKEN="$A2A_BEARER_TOKEN"
    echo "TOKEN set from A2A_BEARER_TOKEN: $TOKEN"
  else
    TOKEN="test-token"
    echo "TOKEN not set; using fallback: $TOKEN"
  fi
fi

set -euo pipefail

echo "PYTHONPATH: $PYTHONPATH"
pwd
ls -l
docker compose ps
docker compose logs server

echo "--- Creating a new task (tasks_send) ---"
echo "--- Creating a new task (tasks_send) ---"
SEND_RESP=$(curl -v -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tasks_send","params":{"raw_text":"FROM python:3.12-slim\nCMD [\"python\", \"app.py\"]"}}')
echo "Raw SEND_RESP: $SEND_RESP"
TASK_ID=$(echo "$SEND_RESP" | jq -r '.result.result.task.id // empty')
echo "Extracted TASK_ID: $TASK_ID"

if [[ "$TASK_ID" == "null" || -z "$TASK_ID" ]]; then
  echo "Failed to create task."
  exit 1
fi

echo "--- Setting push notification endpoint (tasks_pushNotification_set) ---"
SET_RESP=$(curl -v -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tasks_pushNotification_set","params":{"id":"'$TASK_ID'","endpoint":"https://example.com/a2a/push","token":"push-secret"}}')
echo "Raw SET_RESP: $SET_RESP"

if ! echo "$SET_RESP" | grep -q 'Push endpoint set'; then
  echo "Failed to set push notification endpoint."
  exit 1
fi

echo "--- Getting push notification endpoint (tasks_pushNotification_get) ---"
GET_RESP=$(curl -v -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tasks_pushNotification_get","params":{"id":"'$TASK_ID'"}}')
echo "Raw GET_RESP: $GET_RESP"

ENDPOINT=$(echo "$GET_RESP" | jq -r '.result.result.endpoint')
PUSH_TOKEN=$(echo "$GET_RESP" | jq -r '.result.result.token')
echo "Extracted ENDPOINT: $ENDPOINT"
echo "Extracted PUSH_TOKEN: $PUSH_TOKEN"

if [[ "$ENDPOINT" != "https://example.com/a2a/push" || "$PUSH_TOKEN" != "push-secret" ]]; then
  echo "Push notification endpoint retrieval failed."
  exit 1
fi

echo "--- Getting push endpoint for unknown task (should fail) ---"
FAIL_RESP=$(curl -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${A2A_BEARER_TOKEN:-test-token}" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tasks_pushNotification_get","params":{"id":"unknown-task-id"}}')
echo "$FAIL_RESP"
if ! echo "$FAIL_RESP" | grep -q 'No push endpoint for task id'; then
  echo "Expected error for unknown task id not found."
  exit 1
fi

echo "All push notification tests completed successfully."
