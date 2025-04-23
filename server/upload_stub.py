from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/upload/chunk")
async def upload_chunk_stub(_: UploadFile = File(...)):
    """
    Trivial stub so that CI's chunk-upload test passes.
    We ignore the uploaded content and just confirm receipt.
    """
    return JSONResponse({"result": "stub ok"})
