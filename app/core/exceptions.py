from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class APIError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, error_code: str = "BAD_REQUEST"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class ModelNotLoadedError(APIError):
    def __init__(self, message: str = "Model artifact is not loaded or unavailable"):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, error_code="MODEL_NOT_LOADED")



class BatchSizeExceededError(APIError):
    def __init__(self, max_size: int, actual_size: int):
        message = f"Batch size of {actual_size} exceeds maximum allowable size of {max_size}"
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, error_code="BATCH_SIZE_EXCEEDED")


class PredictionError(APIError):
    def __init__(self, message: str):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error_code="PREDICTION_FAILED")


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] APIError ({exc.error_code}): {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.message,
            "request_id": request_id,
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected internal server error occurred.",
            "request_id": request_id,
        }
    )
