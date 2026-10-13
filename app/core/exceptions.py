import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("app.exceptions")


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "Bad Request",
        details: Any = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.details = details or message


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
            "error": {
                "code": exc.status_code,
                "details": exc.details,
            },
        },
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": exc.status_code,
                "details": exc.detail,
            },
        },
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    formatted_errors = []
    for err in exc.errors():
        field_parts = [str(loc) for loc in err.get("loc", []) if loc != "body"]
        formatted_errors.append(
            {
                "field": ".".join(field_parts) if field_parts else "body",
                "message": err.get("msg", "Invalid value"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation failed",
            "data": None,
            "error": {
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": formatted_errors,
            },
        },
    )


async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    logger.error(f"Database IntegrityError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "message": "Resource conflict or constraint violation",
            "data": None,
            "error": {
                "code": status.HTTP_409_CONFLICT,
                "details": "A record with this information already exists or violates a constraint.",
            },
        },
    )


async def global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "data": None,
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "details": "An unexpected error occurred. Please try again later.",
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)
