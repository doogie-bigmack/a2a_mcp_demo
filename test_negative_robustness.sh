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

echo "PYTHONPATH: $PYTHONPATH"
pwd
ls -l
docker compose ps
docker compose logs server

BASE_URL="http://localhost:8080"
AUTH_HEADER="Authorization: Bearer ${A2A_BEARER_TOKEN:-test-token}"

fail() { echo "[FAIL] $1"; exit 1; }
pass() { echo "[PASS] $1"; }

# 1. GET invalid endpoint returns 404
echo "Test: GET to invalid endpoint returns 404"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/.well-known/agent.jsonBAD")
[[ "$code" == 404 ]] && pass "404 for invalid endpoint" || fail "Expected 404, got $code"

# 2. POST/PUT/DELETE to agent.json returns 405
for method in POST PUT DELETE; do
  echo "Test: $method to agent.json returns 405"
  code=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$BASE_URL/.well-known/agent.json" -H "$AUTH_HEADER")
  [[ "$code" == 405 ]] && pass "405 for $method agent.json" || fail "Expected 405, got $code for $method"
done

# 3. Malformed Accept header returns 406 or JSON error
echo "Test: Malformed Accept header returns 406 or JSON error"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/.well-known/agent.json" -H "Accept: application/xml")
[[ "$code" == 406 || "$code" == 400 ]] && pass "406/400 for malformed Accept" || fail "Expected 406/400, got $code"

# 4. No Accept header (should default to JSON)
echo "Test: No Accept header defaults to JSON"
resp=$(curl -s "$BASE_URL/.well-known/agent.json")
echo "$resp" | jq .name >/dev/null && pass "Defaults to JSON" || fail "Did not default to JSON"

# 5. Extra query parameters handled gracefully
echo "Test: Extra query parameters handled gracefully"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/.well-known/agent.json?foo=bar&baz=qux")
[[ "$code" == 200 ]] && pass "Extra params OK" || fail "Expected 200, got $code"

# 6. Validate agent card JSON schema and required fields
echo "Test: Agent card JSON schema and required fields"
resp=$(curl -s "$BASE_URL/.well-known/agent.json")
for field in name url version skills capabilities authentication; do
  echo "$resp" | jq ".$field" >/dev/null || fail "Missing agent card field: $field"
done
pass "Agent card has all required fields"

# 7. JSON-RPC: send malformed request (invalid JSON, missing fields)"
echo "Test: JSON-RPC invalid JSON returns error"
resp=$(curl -s -X POST "$BASE_URL/" -H "Content-Type: application/json" -H "$AUTH_HEADER" -d '{invalid json')
echo "$resp" | grep -q 'error' && pass "Invalid JSON returns error" || fail "Malformed JSON did not return error"

echo "Test: JSON-RPC missing method returns error"
resp=$(curl -v -s -X POST -H "Content-Type: application/json" -H "$AUTH_HEADER" -d '{"jsonrpc":"2.0","id":1,"params":{}}' "$BASE_URL/")
echo "$resp" | grep -q 'error' && pass "Missing method returns error" || fail "Missing method did not return error"

# 8. JSON-RPC: request non-existent task ID returns −32001
echo "Test: JSON-RPC get non-existent task returns -32001"
resp=$(curl -v -s -X POST -H "Content-Type: application/json" -H "$AUTH_HEADER" -d '{"jsonrpc":"2.0","id":2,"method":"tasks_get","params":{"id":"does-not-exist"}}' "$BASE_URL/")
echo "Response for non-existent task: $resp"
err_code=$(echo "$resp" | jq -r '.error.code // empty')
if [[ "$err_code" == "-32001" ]]; then
  pass "Non-existent task returns -32001"
else
  fail "Did not return -32001 for unknown task (got: $err_code)"
fi

# 9. SSE: connect with invalid/expired task ID returns error/close
echo "Test: SSE with invalid task ID closes connection"
code=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$BASE_URL/stream/does-not-exist")
[[ "$code" == 404 || "$code" == 400 ]] && pass "SSE invalid task closes/404" || fail "Expected 404/400, got $code"

echo "All negative/robustness tests passed."
