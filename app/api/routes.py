from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.core.errors import AppError, ErrorCode
from app.pipeline import load_result
from app.schemas.document import FinalDocument
from app.schemas.jobs import StatusResponse, UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    try:
        stored = await request.app.state.upload_manager.save(file)
        request.app.state.job_store.create_job(
            stored.document_id,
            stored.filename,
            stored.document_type,
            stored.path,
        )
    except AppError as exc:
        raise HTTPException(
            status_code=_status_for_error(exc.code),
            detail={"code": exc.code, "message": exc.message, "retryable": exc.retryable},
        ) from exc
    status_payload = request.app.state.job_store.get_status(stored.document_id)
    return UploadResponse(document_id=stored.document_id, status=status_payload.status)


@router.get("/status/{document_id}", response_model=StatusResponse)
async def get_status(request: Request, document_id: str) -> StatusResponse:
    response = request.app.state.job_store.get_status(document_id)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.JOB_NOT_FOUND,
                "message": "Document job was not found.",
                "retryable": False,
            },
        )
    return response


@router.get("/result/{document_id}", response_model=FinalDocument)
async def get_result(request: Request, document_id: str) -> FinalDocument:
    job_status = request.app.state.job_store.get_status(document_id)
    if job_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.JOB_NOT_FOUND,
                "message": "Document job was not found.",
                "retryable": False,
            },
        )
    result_path = request.app.state.job_store.get_result_path(document_id)
    if result_path is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": ErrorCode.RESULT_NOT_READY,
                "message": f"Result is not ready; current status is {job_status.status}.",
                "retryable": job_status.status != "failed",
            },
        )
    return load_result(result_path)


def _status_for_error(code: ErrorCode) -> int:
    if code == ErrorCode.UNSUPPORTED_FILE_TYPE:
        return status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    if code in {ErrorCode.FILE_TOO_LARGE, ErrorCode.EMPTY_FILE}:
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_500_INTERNAL_SERVER_ERROR
