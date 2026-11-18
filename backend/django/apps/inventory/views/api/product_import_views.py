"""Product bulk import endpoints — template download, upload, preview, commit."""
from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.permissions import CanImportProducts
from apps.inventory.services.product_import_service import ProductImportService
from apps.inventory.services.template_builder import build_template
from core.exceptions.domain import ValidationError


ALLOWED_EXTENSIONS = (".xlsx", ".xlsm", ".csv")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class ProductTemplateView(APIView):
    """Download the blank Excel template with dropdowns and sample rows."""

    permission_classes = [CanImportProducts]

    @extend_schema(
        responses={(200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): bytes},
        summary="Download product import template",
    )
    def get(self, request):
        buffer = build_template()
        return FileResponse(
            buffer,
            as_attachment=True,
            filename="demka_product_template.xlsx",
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )


class ProductImportView(APIView):
    """
    POST multipart:
        file        — .xlsx / .xlsm / .csv
        mode        — "preview" (default) or "commit"
        skip_errors — "true" to import only valid rows
    """

    permission_classes = [CanImportProducts]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "mode": {"type": "string", "enum": ["preview", "commit"]},
                    "skip_errors": {"type": "boolean"},
                },
                "required": ["file"],
            }
        },
        responses={200: dict},
    )
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        filename = (getattr(file, "name", "") or "").lower()
        if not filename.endswith(ALLOWED_EXTENSIONS):
            return Response(
                {"detail": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if file.size > MAX_UPLOAD_BYTES:
            return Response(
                {"detail": f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mode = request.data.get("mode", "preview")
        skip_raw = request.data.get("skip_errors", "false")
        skip_errors = str(skip_raw).lower() in ("true", "1", "yes", "on")

        try:
            result = ProductImportService.import_file(
                file, user=request.user, mode=mode, skip_errors=skip_errors,
            )
        except ValidationError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": f"Import failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result, status=status.HTTP_200_OK)