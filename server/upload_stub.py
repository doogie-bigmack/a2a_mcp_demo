import logging
import json
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()

@router.api_route(
    "/upload/chunk",
    methods=["POST", "PUT", "PATCH"],
    status_code=status.HTTP_200_OK,
)
async def upload_chunk_stub(request: Request):
    """
    JSON-RPC stub: accept one chunk (any content-type) and acknowledge it in JSON-RPC format.
    """
    body = await request.body()
    try:
        data = json.loads(body)
        jsonrpc = data.get("jsonrpc")
        method = data.get("method")
        params = data.get("params")
        req_id = data.get("id")
    except Exception as e:
        logging.error(json.dumps({"event": "invalid_json", "error": str(e)}))
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None,
            },
        )

    logging.info(json.dumps({
        "event": "upload_chunk_stub_called",
        "url": str(request.url),
        "method": method,
        "params": params,
        "id": req_id,
    }))

    # Always return JSON-RPC success response (stub)
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "result": "ok",
            "id": req_id,
        }
    )