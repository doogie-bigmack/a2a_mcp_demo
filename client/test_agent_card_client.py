import os
import json

CLIENT_AGENT_CARD_PATH = os.path.join(
    ".well-known", "agent.json"
)
REQUIRED_FIELDS = [
    "name", "url", "version", "skills", "capabilities", "authentication"
]

def test_agent_card_fields():
    with open(CLIENT_AGENT_CARD_PATH, "r") as f:
        card = json.load(f)
    missing = [f for f in REQUIRED_FIELDS if f not in card]
    assert not missing, f"Agent card missing required fields: {missing}"
    assert isinstance(card["name"], str)
    assert isinstance(card["url"], str)
    assert isinstance(card["version"], str)
    assert isinstance(card["skills"], list)
    assert isinstance(card["capabilities"], dict)
    assert isinstance(card["authentication"], dict)
