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

PYTHON_TEST_FILES=(
    "server/test_agent_card.py"
    "client/test_agent_card.py"
    "test_agent_card.py"
)

SHELL_TEST_FILES=(
    "test_jsonrpc_tasks.sh"
    "test_jsonrpc_push_notification.sh"
    "test_negative_robustness.sh"
    "test_streaming_and_resubscribe.sh"
)

PASS=0
FAIL=0
TOTAL=0

PY_PASS=0
PY_FAIL=0
PY_TOTAL=0
SH_PASS=0
SH_FAIL=0
SH_TOTAL=0

for TEST in "${PYTHON_TEST_FILES[@]}"; do
    if [ -f "$TEST" ]; then
        echo "Running Python test: $TEST ..."
        OUTPUT=$(pytest "$TEST" --tb=short --maxfail=1 2>&1)
        EXIT_CODE=$?
        echo "$OUTPUT"
        if [ $EXIT_CODE -eq 0 ]; then
            echo "PASS: $TEST"
            PY_PASS=$((PY_PASS+1))
        else
            echo "FAIL: $TEST"
            PY_FAIL=$((PY_FAIL+1))
        fi
        PY_TOTAL=$((PY_TOTAL+1))
    fi
done

echo "\n--- Running Shell Test Scripts ---"
for TEST in "${SHELL_TEST_FILES[@]}"; do
    if [ -f "$TEST" ]; then
        echo "Running shell test: $TEST ..."
        bash "$TEST"
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo "PASS: $TEST"
            SH_PASS=$((SH_PASS+1))
        else
            echo "FAIL: $TEST"
            SH_FAIL=$((SH_FAIL+1))
        fi
        SH_TOTAL=$((SH_TOTAL+1))
    fi
done

echo "\n==================== Test Summary ===================="
echo "Python test files run: $PY_TOTAL | Passed: $PY_PASS | Failed: $PY_FAIL"
echo "Shell test scripts run: $SH_TOTAL | Passed: $SH_PASS | Failed: $SH_FAIL"

if [ $PY_FAIL -eq 0 ] && [ $SH_FAIL -eq 0 ]; then
    echo "ALL TESTS PASSED ✅"
    exit 0
else
    echo "SOME TESTS FAILED ❌"
    exit 1
fi
