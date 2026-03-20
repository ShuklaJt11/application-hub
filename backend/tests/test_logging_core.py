import json
import logging

from app.core.logging import JsonFormatter, RequestIDFilter, _request_id_var


def test_request_id_filter_injects_context_request_id():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
    token = _request_id_var.set("req-123")

    try:
        result = RequestIDFilter().filter(record)
    finally:
        _request_id_var.reset(token)

    assert result is True
    assert getattr(record, "request_id") == "req-123"


def test_json_formatter_includes_request_id_and_extra_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        "app.middleware.request_id",
        logging.INFO,
        __file__,
        1,
        "Request completed",
        (),
        None,
    )
    record.request_id = "req-123"
    record.method = "GET"
    record.path = "/health"
    record.duration_ms = 12.5

    payload = json.loads(formatter.format(record))

    assert payload["logger"] == "app.middleware.request_id"
    assert payload["message"] == "Request completed"
    assert payload["request_id"] == "req-123"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["duration_ms"] == 12.5
