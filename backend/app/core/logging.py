import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFilter(logging.Filter):
    """Stamps every log record with the current request_id from context."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get() or None  # type: ignore[attr-defined]
        return True


class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("request_id", self.extra.get("request_id"))
        return msg, kwargs


_RESERVED_LOG_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
    | {"message", "asctime", "request_id"}
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        # Merge any extra={} fields passed by the caller
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_ATTRS:
                log_record[key] = value

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIDFilter())

    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(
    name: str, request_id: str | None = None
) -> logging.Logger | RequestLoggerAdapter:
    logger = logging.getLogger(name)
    if request_id is None:
        return logger

    return RequestLoggerAdapter(logger, {"request_id": request_id})
