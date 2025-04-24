import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
import logfire

router = APIRouter()


def event_generator(task_id: str):
    """
    Simulate a server-sent event (SSE) stream of status updates for a given task.

    Args:
        task_id (str): The ID of the task to stream updates for.

    Yields:
        str: SSE-formatted strings containing task state updates.
    """
    states = ["submitted", "working", "completed"]
    for state in states:
        asyncio.sleep(1)
        event = {"task_id": task_id, "state": state}
        yield f"data: {json.dumps(event)}\n\n"
    yield "event: close\ndata: null\n\n"


@router.get("/stream/{task_id}")
def stream_task_status(task_id: str, request: Request):
    """
    Stream status updates for a task using server-sent events (SSE).

    Args:
        task_id (str): The ID of the task to stream.
        request (Request): The incoming FastAPI request.

    Returns:
        StreamingResponse: SSE stream of task status updates, or JSON error if the
        task is unknown.
    """
    from server.task_store import task_store
    import logfire
    logfire.info("sse_all_task_ids", all_task_ids=list(task_store.tasks.keys()), requested_task_id=task_id)
    if task_id not in task_store.tasks:
        logfire.error("stream_invalid_task_id", task_id=task_id)
        return JSONResponse(content={"error": "Task id unknown"}, status_code=404)
    return StreamingResponse(event_generator(task_id), media_type="text/event-stream")
