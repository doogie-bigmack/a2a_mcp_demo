import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from shared.models import Task

router = APIRouter()

async def event_generator(task_id: str):
    # Simulate streaming status updates for demo
    states = ["submitted", "working", "completed"]
    for state in states:
        await asyncio.sleep(1)
        event = {"task_id": task_id, "state": state}
        yield f"data: {json.dumps(event)}\n\n"
    # End of stream
    yield "event: close\ndata: null\n\n"

from task_store import task_store
import logfire
from fastapi.responses import JSONResponse

@router.get("/stream/{task_id}")
async def stream_task_status(task_id: str, request: Request):
    if task_id not in task_store.tasks:
        logfire.error("stream_invalid_task_id", task_id=task_id)
        return JSONResponse(content={"error": "Task id unknown"}, status_code=404)
    return StreamingResponse(event_generator(task_id), media_type="text/event-stream")
