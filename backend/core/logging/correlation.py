"""Thread-local correlation id + middleware + logging filter."""
import uuid
import threading
import logging

_local = threading.local()


def get_correlation_id() -> str:
    return getattr(_local, "correlation_id", "-")


def set_correlation_id(value: str | None = None) -> str:
    cid = value or str(uuid.uuid4())
    _local.correlation_id = cid
    return cid


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cid = request.META.get("HTTP_X_CORRELATION_ID") or set_correlation_id()
        set_correlation_id(cid)
        response = self.get_response(request)
        response["X-Correlation-ID"] = cid
        return response