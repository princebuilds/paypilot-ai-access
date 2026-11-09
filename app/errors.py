"""AppError hierarchy and standardized error handling."""
import logging
from typing import Any, Dict

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("paypilot.errors")


class AppError(Exception):
    """Base application error with standard error envelope fields."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
            }
        }


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="NOT_FOUND", message=message, status_code=status.HTTP_404_NOT_FOUND)


class RateLimitedError(AppError):
    def __init__(self, message: str = "Many people are using this demo. Please wait a minute and try again."):
        super().__init__(
            code="RATE_LIMITED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retryable=True,
        )


class NotImplementedFeatureError(AppError):
    def __init__(self, message: str = "This feature is not implemented yet."):
        super().__init__(
            code="NOT_IMPLEMENTED",
            message=message,
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            retryable=False,
        )


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Handle AppError by emitting SPEC.md section 3 error envelope."""
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with plain language."""
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid input")
    field = ".".join(str(loc) for loc in first_error.get("loc", []) if loc != "body")
    message = f"Invalid input for {field}: {msg}" if field else f"Invalid input: {msg}"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "retryable": False,
            }
        },
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors without leaking stack traces or internal secrets."""
    logger.error("Unhandled exception caught: %s", type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "The assistant is not responding. Please try again.",
                "retryable": True,
            }
        },
    )
