import uuid

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.logging import _request_id_var
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.request_id import RequestIDMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ErrorHandlerMiddleware)  # type: ignore[call-arg,arg-type]
    app.add_middleware(RequestIDMiddleware)  # type: ignore[call-arg,arg-type]

    @app.get("/ok")
    async def ok(request: Request):
        return {
            "request_id": request.state.request_id,
            "context_request_id": _request_id_var.get(),
        }

    @app.get("/boom")
    async def boom():
        raise RuntimeError("boom")

    return app


def test_request_id_middleware_sets_state_and_header():
    client = TestClient(_build_app())

    response = client.get("/ok")

    assert response.status_code == 200
    payload = response.json()
    request_id = response.headers["X-Request-ID"]
    assert request_id == payload["request_id"]
    assert request_id == payload["context_request_id"]
    assert str(uuid.UUID(request_id)) == request_id


def test_error_handler_returns_tracing_data_on_500():
    client = TestClient(_build_app())

    response = client.get("/boom")

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Internal Server Error"
    assert payload["request_id"] == response.headers["X-Request-ID"]


def test_request_context_is_reset_after_request():
    client = TestClient(_build_app())

    client.get("/ok")

    assert _request_id_var.get() == ""
