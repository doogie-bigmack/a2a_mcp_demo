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
  TOKEN="$A2A_BEARER_TOKEN"
  echo "TOKEN set from A2A_BEARER_TOKEN: $TOKEN"
fi

set -euo pipefail

API_URL="http://localhost:8080/"
TOKEN="${A2A_BEARER_TOKEN:-test-token}"

fail() { echo "[FAIL] $1"; exit 1; }
pass() { echo "[PASS] $1"; }

# 1. Create a new task
SEND_RESP=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tasks_send","params":{"raw_text":"FROM python:3.12-slim\nCMD [\"python\", \"app.py\"]"}}')
echo "$SEND_RESP"
TASK_ID=$(echo "$SEND_RESP" | jq -r '.result.task.id')

[[ -z "$TASK_ID" || "$TASK_ID" == "null" ]] && fail "Could not create task"
pass "Task created: $TASK_ID"

# 2. Test streaming endpoint (SSE)
echo "Testing SSE /stream/$TASK_ID ..."
STREAM_RESP=$(curl -s -N "$API_URL/stream/$TASK_ID")
echo "$STREAM_RESP" | grep -q 'submitted' && pass "SSE stream contains 'submitted'" || fail "SSE stream missing 'submitted'"

# 3. Test resubscribe JSON-RPC
RESUBSCRIBE_RESP=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tasks_resubscribe","params":{"id":"'$TASK_ID'","historyLength":0}}')
echo "$RESUBSCRIBE_RESP"
STREAM_URL=$(echo "$RESUBSCRIBE_RESP" | jq -r '.result.stream_url // .stream_url')
[[ "$STREAM_URL" == "/stream/$TASK_ID" ]] && pass "Resubscribe returns correct stream_url" || fail "Resubscribe stream_url incorrect: $STREAM_URL"

TRANSITIONS_COUNT=$(echo "$RESUBSCRIBE_RESP" | jq '.result.transitions | length')
[[ "$TRANSITIONS_COUNT" -ge 1 ]] && pass "Resubscribe returns transitions" || fail "No transitions in resubscribe"

# 4. Test chunked upload stub
CHUNKED_RESP=$(curl -s -X POST "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"chunked_upload_stub","params":{}}')
echo "$CHUNKED_RESP" | grep -q 'not implemented' && pass "Chunked upload stub returns not implemented" || fail "Chunked upload stub did not return expected message"

# 5. Test artifacts/parts structure in resubscribe (should always be present, may be empty)
ARTIFACTS=$(echo "$RESUBSCRIBE_RESP" | jq '.result.artifacts // .artifacts')
[[ "$ARTIFACTS" != "null" ]] && pass "Artifacts returned in resubscribe" || fail "No artifacts in resubscribe"

# 6. Test SSE with invalid task id
INVALID_STREAM=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/stream/does-not-exist")
[[ "$INVALID_STREAM" == "404" || "$INVALID_STREAM" == "400" ]] && pass "SSE invalid task id returns error/close" || fail "Expected 404/400 for invalid SSE task id, got $INVALID_STREAM"

echo "All streaming, resubscribe, chunked upload, and artifact tests passed."
