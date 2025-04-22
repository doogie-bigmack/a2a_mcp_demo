#!/bin/bash
set -euo pipefail

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
resp=$(curl -s -X POST "$BASE_URL/" -H "Content-Type: application/json" -H "$AUTH_HEADER" -d '{"jsonrpc":"2.0","id":1,"params":{}}')
echo "$resp" | grep -q 'error' && pass "Missing method returns error" || fail "Missing method did not return error"

# 8. JSON-RPC: request non-existent task ID returns −32001
echo "Test: JSON-RPC get non-existent task returns -32001"
resp=$(curl -s -X POST "$BASE_URL/" -H "Content-Type: application/json" -H "$AUTH_HEADER" -d '{"jsonrpc":"2.0","id":2,"method":"tasks_get","params":{"id":"does-not-exist"}}')
echo "$resp" | grep -q '32001' && pass "Non-existent task returns -32001" || fail "Did not return -32001 for unknown task"

# 9. SSE: connect with invalid/expired task ID returns error/close
echo "Test: SSE with invalid task ID closes connection"
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/stream/does-not-exist")
[[ "$code" == 404 || "$code" == 400 ]] && pass "SSE invalid task closes/404" || fail "Expected 404/400, got $code"

echo "All negative/robustness tests passed."
