import logging

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)

        except Exception:
            logger.exception(
                "Unhandled error",
                extra={"request_id": getattr(request.state, "request_id", None)},
            )

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
