"""Shared helpers for read-only reporting endpoints."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reporting.permissions import CanViewReports
from apps.reporting.services.date_utils import parse_range, previous_period
from apps.reporting.services.exports import dicts_to_csv


class ReportingAPIView(APIView):
    permission_classes = [CanViewReports]
    csv_filename = "report.csv"

    def resolve_range(self, request):
        return parse_range(request)

    def wants_csv(self, request) -> bool:
        return request.query_params.get("format", "").lower() == "csv"

    def csv_or_json(self, request, rows, filename=None):
        if self.wants_csv(request) and isinstance(rows, list):
            return dicts_to_csv(rows, filename or self.csv_filename)
        return Response(rows)

    def period_response(self, request, start, end, builder, filename=None):
        """Handle JSON/CSV and attach a previous-period report when requested."""
        current = builder(start, end)
        if self.wants_csv(request) and isinstance(current, list):
            return dicts_to_csv(current, filename or self.csv_filename)
        if request.query_params.get("compare", "").lower() in ("1", "true", "yes"):
            previous_start, previous_end = previous_period(start, end)
            previous = builder(previous_start, previous_end)
            period = {"start": previous_start.isoformat(), "end": previous_end.isoformat()}
            if isinstance(current, dict):
                current = {**current, "comparison": {"period": period, "data": previous}}
            else:
                current = {
                    "period": {"start": start.isoformat(), "end": end.isoformat()},
                    "results": current,
                    "comparison": {"period": period, "results": previous},
                }
        return Response(current)

    @staticmethod
    def bad_request(message: str):
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def integer_param(request, key, default, *, minimum=1, maximum=1000):
        try:
            value = int(request.query_params.get(key, default))
        except (TypeError, ValueError):
            raise ValueError(f"{key} must be an integer.")
        if not minimum <= value <= maximum:
            raise ValueError(f"{key} must be between {minimum} and {maximum}.")
        return value
