print('CLIENT AGENT LOADED')
import os
import logfire
import requests
import json
from shared.models import DockerConfig

try:
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

app = FastAPI() if FASTAPI_AVAILABLE else None

if FASTAPI_AVAILABLE:
    @app.get("/.well-known/agent.json")
    def get_agent_card():
        agent_card_path = os.path.join(os.path.dirname(__file__), ".well-known", "agent.json")
        return FileResponse(agent_card_path, media_type="application/json")

logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    service_name="client_agent",
    send_to_logfire="if-token-present",
    console=logfire.ConsoleOptions(span_style="simple")
)
GREEN = "\033[92m"
RESET = "\033[0m"

def green_log(msg):
    if isinstance(msg, dict):
        import json
        print(f"{GREEN}{json.dumps(msg)}{RESET}")
    else:
        print(f"{GREEN}{msg}{RESET}")

class A2AClient:
    """
    Client for communicating with an A2A-compliant agent server using JSON-RPC over HTTP.
    Handles agent card validation, sending Dockerfile content, and error reporting with logfire.

    Attributes:
        server_url (str): The URL of the agent server.
        bearer_token (str): Bearer token for authentication.
        agent_card (dict): Validated agent card metadata from the server.
    """
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.bearer_token = os.getenv("A2A_BEARER_TOKEN", "test-token")
        self.agent_card = self.fetch_and_validate_server_agent_card()

    def fetch_and_validate_server_agent_card(self):
        """Fetch and validate the server's agent card."""
        url = self.server_url.rstrip('/') + '/.well-known/agent.json'
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            card = resp.json()
            required_fields = ["name", "url", "version", "skills", "capabilities", "authentication"]
            missing = [f for f in required_fields if f not in card]
            if missing:
                logfire.error("agent_card_missing_fields", missing=missing, card=card)
                raise ValueError(f"Server agent card missing required fields: {missing}")
            # Optionally, validate types/values here
            logfire.info("agent_card_validated", card=card)
            green_log({"event": "agent_card_validated", "card": card})
            return card
        except Exception as e:
            logfire.error("agent_card_validation_failed", error=str(e), url=url)
            green_log({"event": "agent_card_validation_failed", "error": str(e), "url": url})
            raise

    def send_dockerfile(self, dockerfile_text: str):
        # JSON-RPC 2.0 payload
        rpc_payload = {
            "jsonrpc": "2.0",
            "method": "tasks_send",
            "params": {"raw_text": dockerfile_text},
            "id": 1
        }
        logfire.info("send_dockerfile", payload=rpc_payload)
        green_log({"event": "send_dockerfile", "payload": rpc_payload})
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        try:
            resp = requests.post(f"{self.server_url}/", json=rpc_payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            if "error" in result:
                logfire.error("client_jsonrpc_error", error=result["error"])
                green_log({"event": "client_jsonrpc_error", "error": result["error"]})
                return {"error": result["error"]}
            logfire.info("received_response", response=result.get("result"))
            green_log({"event": "received_response", "response": result.get("result")})
            return result.get("result")
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = resp.json()
            except Exception:
                error_detail = resp.text
            logfire.error("client_http_error", status_code=resp.status_code, body=error_detail)
            green_log({"event": "client_http_error", "status_code": resp.status_code, "body": error_detail})
            return {"error": f"HTTP {resp.status_code}: {error_detail}"}
        except Exception as e:
            logfire.error("client_exception", error=str(e))
            green_log({"event": "client_exception", "error": str(e)})
            return {"error": str(e)}
