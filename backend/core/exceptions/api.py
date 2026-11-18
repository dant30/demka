"""DRF global exception handler — understands DomainError."""
import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from core.exceptions.domain import DomainError


DOMAIN_STATUS = {
    "not_found": status.HTTP_404_NOT_FOUND,
    "validation_error": status.HTTP_400_BAD_REQUEST,
    "business_rule_violation": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "conflict": status.HTTP_409_CONFLICT,
    "insufficient_stock": status.HTTP_409_CONFLICT,
    "credit_limit_exceeded": status.HTTP_409_CONFLICT,
}

logger = logging.getLogger(__name__)


def _body(code: int, message, details=None):
    body = {"success": False, "error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def demka_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        http_status = DOMAIN_STATUS.get(exc.code, status.HTTP_400_BAD_REQUEST)
        return Response(_body(http_status, exc.message, exc.details), status=http_status)

    response = exception_handler(exc, context)
    if response is not None:
        return Response(_body(response.status_code, response.data), status=response.status_code)

    request = context.get("request")
    logger.exception(
        "Unhandled API exception (%s %s)",
        getattr(request, "method", "?"),
        getattr(request, "path", "?"),
    )
    return Response(
        _body(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error."),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )