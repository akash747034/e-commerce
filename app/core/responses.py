from typing import Any

from fastapi import status
from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
            "error": None,
        },
    )


def error_response(
    message: str = "An error occurred",
    error: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": error if error is not None else {"code": status_code, "details": message},
        },
    )
