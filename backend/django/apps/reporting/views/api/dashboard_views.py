"""Cached dashboard endpoint."""
import logging

from django.core.cache import cache
from rest_framework.response import Response

from .base import ReportingAPIView
from apps.reporting.services.dashboard_service import DashboardService


logger = logging.getLogger(__name__)


class DashboardView(ReportingAPIView):
    def get(self, request):
        cache_key = "reporting:dashboard:v1"
        try:
            payload = cache.get(cache_key)
        except Exception:
            logger.warning("Reporting dashboard cache unavailable; building live.", exc_info=True)
            payload = None
        if payload is None:
            payload = DashboardService.build()
            try:
                cache.set(cache_key, payload, timeout=300)
            except Exception:
                logger.warning("Could not cache reporting dashboard.", exc_info=True)
        return Response(payload)
