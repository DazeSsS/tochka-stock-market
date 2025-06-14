from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.exceptions.schemas import ErrorResponse, NotFoundResponse
from app.api.exceptions.exceptions import (
    AccessDeniedException,
    InvalidAPIKeyException,
    InvalidAuthorizationFormatException,
    NotFoundException
)


def set_exceptions(app: FastAPI):
    @app.exception_handler(AccessDeniedException)
    async def access_denied_exception_handler(request: Request, exc: AccessDeniedException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(detail=exc.detail).model_dump()
        )

    @app.exception_handler(InvalidAPIKeyException)
    async def invalid_key_exception_handler(request: Request, exc: InvalidAPIKeyException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(detail=exc.detail).model_dump()
        )

    @app.exception_handler(InvalidAuthorizationFormatException)
    async def invallid_auth_format_exception_handler(request: Request, exc: InvalidAuthorizationFormatException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(detail=exc.detail).model_dump()
        )

    @app.exception_handler(NotFoundException)
    async def not_found_exception_handler(request: Request, exc: NotFoundException):
        return JSONResponse(
            status_code=exc.status_code,
            content=NotFoundResponse(detail=exc.detail).model_dump()
        )
