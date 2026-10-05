from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse

class ErrorCode:
    INVALID_URL = "INVALID_URL"
    REPO_NOT_FOUND = "REPO_NOT_FOUND"
    REPO_PRIVATE = "REPO_PRIVATE"
    REPO_EMPTY = "REPO_EMPTY"
    REPO_TOO_LARGE = "REPO_TOO_LARGE"
    GITHUB_RATE_LIMITED = "GITHUB_RATE_LIMITED"
    LLM_FAILED = "LLM_FAILED"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL = "INTERNAL"

class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
            }
        }
        if self.details:
            result["error"]["details"] = self.details
        return result

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log unexpected internal errors server-side without exposing internals
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.INTERNAL,
                "message": "Something went wrong on our side. Try again.",
                "retryable": True,
            }
        },
    )
