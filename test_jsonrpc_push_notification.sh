#!/bin/bash
set -euo pipefail

echo "--- Creating a new task (tasks_send) ---"
SEND_RESP=$(curl -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${A2A_BEARER_TOKEN:-test-token}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tasks_send","params":{"raw_text":"FROM python:3.12-slim\nCMD [\"python\", \"app.py\"]"}}')
echo "$SEND_RESP"
TASK_ID=$(echo "$SEND_RESP" | jq -r '.result.task.id')

if [[ "$TASK_ID" == "null" || -z "$TASK_ID" ]]; then
  echo "Failed to create task."
  exit 1
fi

echo "--- Setting push notification endpoint (tasks_pushNotification_set) ---"
SET_RESP=$(curl -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${A2A_BEARER_TOKEN:-test-token}" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tasks_pushNotification_set","params":{"id":"'$TASK_ID'","endpoint":"https://example.com/a2a/push","token":"push-secret"}}')
echo "$SET_RESP"

if ! echo "$SET_RESP" | grep -q 'Push endpoint set'; then
  echo "Failed to set push notification endpoint."
  exit 1
fi

echo "--- Getting push notification endpoint (tasks_pushNotification_get) ---"
GET_RESP=$(curl -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${A2A_BEARER_TOKEN:-test-token}" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tasks_pushNotification_get","params":{"id":"'$TASK_ID'"}}')
echo "$GET_RESP"

ENDPOINT=$(echo "$GET_RESP" | jq -r '.result.endpoint')
TOKEN=$(echo "$GET_RESP" | jq -r '.result.token')

if [[ "$ENDPOINT" != "https://example.com/a2a/push" || "$TOKEN" != "push-secret" ]]; then
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
