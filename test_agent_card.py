import os
import pytest
import json

CLIENT_AGENT_CARD_PATH = os.path.join("client", ".well-known", "agent.json")
SERVER_AGENT_CARD_PATH = os.path.join("server", ".well-known", "agent.json")

REQUIRED_FIELDS = ["name", "url", "version", "skills", "capabilities", "authentication"]

@pytest.mark.parametrize("path", [CLIENT_AGENT_CARD_PATH, SERVER_AGENT_CARD_PATH])
def test_agent_card_fields(path):
    with open(path, "r") as f:
        card = json.load(f)
    missing = [f for f in REQUIRED_FIELDS if f not in card]
    assert not missing, f"Agent card {path} missing required fields: {missing}"
    # Optionally check types
    assert isinstance(card["name"], str)
    assert isinstance(card["url"], str)
    assert isinstance(card["version"], str)
    assert isinstance(card["skills"], list)
    assert isinstance(card["capabilities"], dict)
    assert isinstance(card["authentication"], dict)
