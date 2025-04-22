import inspect
import json

def get_jsonrpc_method_map():
    # Import locally to avoid circular import
    from agent import tasks_send, tasks_get, tasks_cancel, tasks_pushNotification_set, tasks_pushNotification_get
    return {
        "tasks_send": tasks_send,
        "tasks_get": tasks_get,
        "tasks_cancel": tasks_cancel,
        "tasks_pushNotification_set": tasks_pushNotification_set,
        "tasks_pushNotification_get": tasks_pushNotification_get,
    }

async def jsonrpc_async_dispatch(raw_body: bytes):
    try:
        req = json.loads(raw_body.decode("utf-8"))
        method = req.get("method")
        params = req.get("params", {})
        req_id = req.get("id")
        methods = get_jsonrpc_method_map()
        if method not in methods:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method {method} not found"}
            }
        func = methods[method]
        # Support both async and sync functions
        if inspect.iscoroutinefunction(func):
            result = await func(**params)
        else:
            result = func(**params)
        if "error" in result:
            return {"jsonrpc": "2.0", "id": req_id, "error": result["error"]}
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req.get("id") if 'req' in locals() else None,
            "error": {"code": -32603, "message": str(e)}
        }
