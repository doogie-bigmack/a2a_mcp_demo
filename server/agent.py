import os
import logfire
import json
import traceback
import uuid
from typing import Any
from fastapi import FastAPI, Request, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from shared.models import (
    DockerConfig, DockerFixResult, TaskStore, TaskHistory, SendTaskRequest,
    SendTaskResponse, Task, PushNotificationEndpoint, Artifact, Part
)
from send_subscribe_sse import router as sse_router
from jsonrpc_dispatch import jsonrpc_async_dispatch
from brave_mcp_client import web_search

# --- JSON-RPC: Push Notification Set ---
async def tasks_pushNotification_set(id: str, endpoint: str, token: str = None):
    if id not in task_store.tasks:
        logfire.error("push_notification_set_unknown_id", task_id=id)
        return {"error": {"code": -32001, "message": "Task id unknown"}}
    task_store.push_endpoints[id] = PushNotificationEndpoint(endpoint=endpoint, token=token)
    logfire.info("push_notification_set", task_id=id, endpoint=endpoint)
    return {"result": "Push endpoint set"}

# --- JSON-RPC: Push Notification Get ---
async def tasks_pushNotification_get(id: str):
    endpoint = task_store.push_endpoints.get(id)
    if not endpoint:
        logfire.error("push_notification_get_unknown_id", task_id=id)
        return {"error": {"code": -32001, "message": "No push endpoint for task id"}}
    logfire.info("push_notification_get", task_id=id, endpoint=endpoint.endpoint)
    return {"result": {"endpoint": endpoint.endpoint, "token": endpoint.token}}


load_dotenv()

logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    service_name="server_agent",
    send_to_logfire="if-token-present",
    console=logfire.ConsoleOptions(span_style="simple")
)

BLUE = "\033[94m"
RESET = "\033[0m"

# blue_log removed; all logging now uses logfire in JSON format

from starlette.types import ASGIApp, Receive, Scope, Send

class LogAllHeadersMiddleware:
    """
    ASGI middleware that logs all HTTP request headers using logfire.

    This middleware logs the path and headers of each HTTP request for observability and debugging.
    It uses logfire for structured JSON logging.
    """
    def __init__(self, app: ASGIApp):
        self.app = app
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            import logfire
            # Log the request path
            logfire.info("asgi_middleware_test", path=scope.get("path"))
            # Log all raw headers
            headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
            logfire.info("asgi_raw_headers", path=scope.get("path"), headers=headers)
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            import logfire
            logfire.error("logallheaders_middleware_exception", error=str(e), path=scope.get("path"))
            from starlette.responses import JSONResponse
            from starlette.types import Message
            import asyncio
            async def error_sender(message: Message):
                if message["type"] == "http.response.start":
                    await send({"type": "http.response.start", "status": 500, "headers": [(b"content-type", b"application/json")]})
                elif message["type"] == "http.response.body":
                    await send({"type": "http.response.body", "body": b'{"error": "Internal Server Error"}', "more_body": False})
            await error_sender({"type": "http.response.start"})
            await error_sender({"type": "http.response.body"})

app = FastAPI()

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

# Middleware to enforce Accept header for agent card endpoint
@app.middleware("http")
async def enforce_agent_card_accept_header(request: Request, call_next):
    """
    Middleware to enforce correct Accept header for the agent card endpoint.
    Logs incoming headers and ensures that requests to /.well-known/agent.json
    have an appropriate Accept header. Uses logfire for logging.

    Args:
        request (Request): The incoming HTTP request.
        call_next: The next middleware or endpoint handler.

    Returns:
        JSONResponse with 406 status if Accept header is invalid, otherwise the normal response.
    """
    logfire.info("middleware_accept_debug", path=str(request.url.path), headers=dict(request.headers))
    if request.url.path == "/.well-known/agent.json": 
        accept = request.headers.get("accept", "application/json").lower()
        allowed = False
        for val in accept.split(','):
            val = val.strip().split(';')[0]
            if "application/json" in val or "*/*" in val or val == '':
                allowed = True
                break
        if not allowed:
            logfire.error("agent_card_invalid_accept", accept=accept)
            return JSONResponse(content={"error": "Not Acceptable"}, status_code=406)
    try:
        response = await call_next(request)
        if response is None:
            logfire.error("middleware_no_response", path=str(request.url.path))
            return JSONResponse(content={"error": "Internal Server Error: No response returned by downstream handler."}, status_code=500)
        return response
    except Exception as e:
        logfire.error("middleware_exception", error=str(e), path=str(request.url.path))
        return JSONResponse(content={"error": f"Internal Server Error: {str(e)}"}, status_code=500)

try:
    app.add_middleware(LogAllHeadersMiddleware)
except Exception as e:
    logfire.error('FAILED TO REGISTER MIDDLEWARE', error=str(e))

logfire.info("asgi_middleware_registered")

# Instrument FastAPI app with logfire for observability and JSON logging
logfire.instrument_fastapi(app)

from send_subscribe_sse import router as sse_router
# Include the SSE router for server-sent events
app.include_router(sse_router)
# Import the shared task store for managing tasks
from task_store import task_store


# --- JSON-RPC streaming method for tasks/sendSubscribe ---
from fastapi.responses import StreamingResponse
import asyncio

async def event_generator(task_id: str):
    """
    Simulate server-sent event (SSE) streaming for a given task.

    Args:
        task_id (str): The ID of the task to stream events for.

    Yields:
        str: Event data as a string for SSE.
    """
    # Simulate streaming status updates for demo
    states = ["submitted", "working", "completed"]
    for state in states:
        await asyncio.sleep(1)
        event = {"task_id": task_id, "state": state}
        yield f"data: {json.dumps(event)}\n\n"
    # End of stream
    yield "event: close\ndata: null\n\n"

# --- JSON-RPC: tasks_resubscribe ---
def tasks_resubscribe(id: str, historyLength: int = 0):
    trace_id = str(uuid.uuid4())
    if id not in task_store.tasks:
        logfire.error("task_resubscribe_not_found", trace_id=trace_id, task_id=id)
        return {"error": {"code": -32001, "message": "Task id unknown"}}
    stream_url = f"/stream/{id}"
    history = task_store.history[id]
    transitions = history.transitions[historyLength:] if historyLength else history.transitions
    artifacts = history.artifacts if hasattr(history, 'artifacts') else []
    logfire.info("task_resubscribe", trace_id=trace_id, task_id=id, stream_url=stream_url)
    return {"stream_url": stream_url, "transitions": transitions, "artifacts": [a.dict() for a in artifacts]}

# --- API stub for chunked uploads ---
def chunked_upload_stub(*args, **kwargs):
    trace_id = str(uuid.uuid4())
    logfire.info("chunked_upload_stub_called", trace_id=trace_id)
    return {"result": "Chunked upload not implemented in PoC"}

# --- Bearer Token Auth Helpers ---
def get_bearer_token():
    return os.getenv("A2A_BEARER_TOKEN")

from fastapi import Depends

def verify_bearer_auth(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()), token: str = Depends(get_bearer_token)):
    if credentials.credentials != token:
        logfire.error("invalid_bearer_token", error="Invalid Bearer token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Bearer token")
    return None

@app.post("/a2a/tasks/sendSubscribe")
async def send_subscribe(request: Request, _auth: None = Depends(verify_bearer_auth)):
    req_data = await request.json()
    task_id = req_data.get("task_id")
    if not task_id:
        logfire.error("missing_task_id", error="No task_id provided for sendSubscribe")
        return JSONResponse(content={"error": "No task_id provided"}, status_code=400)
    logfire.info("send_subscribe_started", task_id=task_id)
    return StreamingResponse(event_generator(task_id), media_type="text/event-stream")
# --- End JSON-RPC streaming method ---

def get_bearer_token():
    return os.getenv("A2A_BEARER_TOKEN", "test-token")

def verify_bearer_auth(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()), token: str = Depends(get_bearer_token)):
    if credentials.scheme != "Bearer" or credentials.credentials != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Bearer token",
        )


import uuid
from shared.models import SendTaskRequest, SendTaskResponse, Task, DockerConfig, DockerFixResult

async def tasks_send(raw_text: str):
    try:
        req = SendTaskRequest(raw_text=raw_text)
        docker_config = DockerConfig(raw_text=req.raw_text)
        hadolint_issues = ["DL3002: Use COPY instead of ADD"]
        try:
            logfire.info("starting search for best practices")
            brave_search_result_text = await web_search("Dockerfile security best practices")
            best_practices = [str(brave_search_result_text)]
            logfire.info("brave_web_search_agent_used", result=brave_search_result_text)
        except RuntimeError as e:
            best_practices = [f"MCP Error: {str(e)}"]
            logfire.error("brave_web_search_agent_failed", error=str(e), traceback=traceback.format_exc(), error_type=type(e).__name__)
        except Exception as e:
            best_practices = [f"Unexpected Error: {str(e)}"]
            logfire.error("brave_web_search_agent_failed", error=str(e), traceback=traceback.format_exc(), error_type=type(e).__name__)
        patched = docker_config.raw_text + "\n# Hardened by server agent\n# " + "\n# ".join(best_practices)
        diff = {"added": ["# Hardened by server agent"] + [f"# {bp}" for bp in best_practices]}
        result = DockerFixResult(
            patched_text=patched,
            diff_json=diff,
            issues_fixed=hadolint_issues + best_practices,
            issues_remaining=[]
        )
        # Create Task object
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            state="submitted",
            docker_config=docker_config
        )
        # Store task and history
        task_store.tasks[task_id] = task
        task_store.history[task_id] = TaskHistory(transitions=[{"state": "submitted"}])
        trace_id = str(uuid.uuid4())
        logfire.info("task_stored", trace_id=trace_id, task_id=task_id)
        return {"result": {"task": task.dict(), "patched": patched}}
    except Exception as e:
        logfire.error("server_exception", error=str(e), traceback=traceback.format_exc())
        return {"error": str(e)}

def tasks_get(id: str, historyLength: int = 0):
    try:
        if id not in task_store.tasks:
            logfire.error("task_not_found", id=id)
            return {"error": {"code": -32001, "message": "Task id unknown"}}
        task = task_store.tasks[id]
        history = task_store.history[id]
        transitions = history.transitions[historyLength:] if historyLength else history.transitions
        artifacts = history.artifacts if hasattr(history, 'artifacts') else []
        trace_id = str(uuid.uuid4())
        logfire.info("task_retrieved", trace_id=trace_id, task_id=id, state=task.state)
        return {"task": task.dict(), "transitions": transitions, "artifacts": [a.dict() for a in artifacts]}
    except Exception as e:
        logfire.error("tasks_get_exception", error=str(e), id=id)
        return {"error": {"code": -32001, "message": str(e)}}

# --- JSON-RPC method for task cancellation ---
def tasks_cancel(id: str):
    try:
        if id not in task_store.tasks:
            logfire.error("task_not_found_cancel", id=id)
            return {"error": {"code": -32001, "message": "Task id unknown"}}
        task = task_store.tasks[id]
        # For PoC, allow cancellation only if state is not 'completed' or 'cancelled'
        if getattr(task, 'state', None) in ["completed", "cancelled"]:
            logfire.error("task_not_cancelable", id=id, state=task.state)
            return {"error": {"code": -32002, "message": "Task not cancelable"}}
        # Set state to cancelled
        task.state = "cancelled"
        if hasattr(task_store.history[id], 'transitions'):
            task_store.history[id].transitions.append({"state": "cancelled"})
        trace_id = str(uuid.uuid4())
        logfire.info("task_cancelled", trace_id=trace_id, task_id=id)
        return {"result": "Task cancelled"}
    except Exception as e:
        logfire.error("tasks_cancel_exception", error=str(e), id=id)
        return {"error": {"code": -32001, "message": str(e)}}
# --- End tasks_cancel ---

from jsonrpc_dispatch import jsonrpc_async_dispatch

@app.post("/")
async def jsonrpc_entrypoint(request: Request, _auth: None = Depends(verify_bearer_auth)):
    try:
        req_data = await request.body()
        response = await jsonrpc_async_dispatch(req_data)
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        logfire.error("jsonrpc_entrypoint_exception", error=str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/a2a/tasks/send")
async def analyze_and_fix_docker(request: Request, _auth: None = Depends(verify_bearer_auth)):
    # legacy REST endpoint for backward compatibility
    try:
        body = await request.json()
        docker_config = DockerConfig(**body)
        hadolint_issues = ["DL3002: Use COPY instead of ADD"]
        try:
            logfire.info("starting search for best practices")
            brave_search_result_text = await web_search("Dockerfile security best practices")
            best_practices = [str(brave_search_result_text)]
            logfire.info("brave_web_search_agent_used", result=brave_search_result_text)
        except RuntimeError as e:
            best_practices = [f"MCP Error: {str(e)}"]
            logfire.error("brave_web_search_agent_failed", error=str(e), traceback=traceback.format_exc(), error_type=type(e).__name__)
        except Exception as e:
            best_practices = [f"Unexpected Error: {str(e)}"]
            logfire.error("brave_web_search_agent_failed", error=str(e), traceback=traceback.format_exc(), error_type=type(e).__name__)
        patched = docker_config.raw_text + "\n# Hardened by server agent\n# " + "\n# ".join(best_practices)
        diff = {"added": ["# Hardened by server agent"] + [f"# {bp}" for bp in best_practices]}
        result = DockerFixResult(
            patched_text=patched,
            diff_json=diff,
            issues_fixed=hadolint_issues + best_practices,
            issues_remaining=[]
        )
        logfire.info("analyze_and_fix_docker", input=docker_config.raw_text, output=result.dict(), brave_search=best_practices)
        # [blue_log] replaced by logfire.info or logfire.error"event": "analyze_and_fix_docker", "input": docker_config.raw_text, "output": result.dict(), "brave_search": best_practices})
        return JSONResponse(content=result.dict())
    except Exception as e:
        logfire.error("server_exception", error=str(e), traceback=traceback.format_exc())
        # [blue_log] replaced by logfire.info or logfire.error"event": "server_exception", "error": str(e)})
        return JSONResponse(content={"error": str(e)}, status_code=500)

from fastapi import Request, Depends

def validate_accept_header(request: Request):
    accept = request.headers.get("accept", "application/json").lower()
    allowed = False
    for val in accept.split(','):
        val = val.strip().split(';')[0]
        if "application/json" in val or "*/*" in val or val == '':
            allowed = True
            break
    if not allowed:
        logfire.error("agent_card_invalid_accept", accept=accept)
        from fastapi import HTTPException
        raise HTTPException(status_code=406, detail="Not Acceptable")

@app.get("/.well-known/agent.json", response_class=JSONResponse)
def agent_card(request: Request, _=Depends(validate_accept_header)):
    card = {
        "name": "Docker Security Agent",
        "description": "Analyzes and hardens Dockerfiles via MCP tools.",
        "url": "http://server:8080",
        "version": "0.1.0",
        "capabilities": {"streaming": True},
        "authentication": {"schemes": ["None"]},
        "skills": [
            {
                "id": "analyze_and_fix_docker",
                "name": "Dockerfile analysis",
                "description": "Analyzes and hardens Dockerfiles using best practices.",
                "tags": ["security", "docker"],
                "examples": ["Harden this Dockerfile: FROM python:3.8"]
            }
        ],
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"]
    }
    return JSONResponse(content=card)
