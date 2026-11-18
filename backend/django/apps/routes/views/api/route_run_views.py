from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import LargePagination
from apps.routes.models import RouteRun
from apps.routes.permissions import (
    CanMaterializeRuns,
    CanOperateRun,
    CanViewRoutes,
)
from apps.routes.serializers import (
    MaterializeSerializer,
    RouteRunCancelSerializer,
    RouteRunCompleteSerializer,
    RouteRunCreateSerializer,
    RouteRunDetailSerializer,
    RouteRunListSerializer,
)
from apps.routes.services import RouteReportingService, RouteRunService


class RunFilterSet(django_filters.FilterSet):
    route = django_filters.NumberFilter()
    agent = django_filters.NumberFilter()
    status = django_filters.CharFilter()
    date_after = django_filters.DateFilter(field_name="run_date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="run_date", lookup_expr="lte")

    class Meta:
        model = RouteRun
        fields = ("route", "agent", "status")


class RouteRunViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        RouteRun.objects
        .select_related("route", "agent", "stock_location", "started_by", "completed_by")
        .all()
    )
    pagination_class = LargePagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_class = RunFilterSet
    ordering_fields = ("run_date", "created_at" if False else "run_date", "status")
    ordering = ["-run_date", "-id"]
    http_method_names = ["get", "post", "head", "options"]  # lifecycle via actions

    def get_permissions(self):
        if self.action == "materialize":
            return [CanMaterializeRuns()]
        if self.action in ("start", "complete", "cancel"):
            return [CanOperateRun()]
        if self.action == "create":
            return [CanMaterializeRuns()]  # single run creation = boss
        return [CanViewRoutes()]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteRunListSerializer
        if self.action == "create":
            return RouteRunCreateSerializer
        if self.action == "complete":
            return RouteRunCompleteSerializer
        if self.action == "cancel":
            return RouteRunCancelSerializer
        if self.action == "materialize":
            return MaterializeSerializer
        return RouteRunDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == "FIELD_AGENT":
            qs = qs.filter(agent=user)
        return qs

    # ---- Override create -----------------------------------
    def create(self, request, *args, **kwargs):
        s = RouteRunCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        run = RouteRunService.create(s.validated_data, request.user)
        return Response(
            RouteRunDetailSerializer(run).data, status=status.HTTP_201_CREATED,
        )

    # ---- Actions -------------------------------------------
    @action(detail=True, methods=["post"], url_path="start")
    def start(self, request, pk=None):
        run = self.get_object()
        self.check_object_permissions(request, run)
        run = RouteRunService.start(run.pk, request.user)
        return Response(RouteRunDetailSerializer(run).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        run = self.get_object()
        self.check_object_permissions(request, run)
        s = RouteRunCompleteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        run = RouteRunService.complete(run.pk, request.user, s.validated_data)
        return Response(RouteRunDetailSerializer(run).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        run = self.get_object()
        self.check_object_permissions(request, run)
        s = RouteRunCancelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        run = RouteRunService.cancel(
            run.pk, request.user, s.validated_data.get("reason", ""),
        )
        return Response(RouteRunDetailSerializer(run).data)

    @action(detail=False, methods=["post"], url_path="materialize")
    def materialize(self, request):
        s = MaterializeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        created = RouteRunService.materialize_range(
            s.validated_data["start_date"], s.validated_data["end_date"],
        )
        return Response(
            {"created": len(created), "ids": [r.pk for r in created]},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="reconciliation")
    def reconciliation(self, request, pk=None):
        return Response(RouteReportingService.run_reconciliation(int(pk)))

    @action(detail=False, methods=["get"], url_path="variance-report")
    def variance_report(self, request):
        from datetime import date, timedelta

        days_back = int(request.query_params.get("days_back", 7))
        today = date.today()
        start = today - timedelta(days=days_back)
        return Response(RouteReportingService.variance_report(start, today))

    @action(detail=False, methods=["get"], url_path="agent-performance")
    def agent_performance(self, request):
        from datetime import date

        agent_id = request.query_params.get("agent")
        if not agent_id:
            return Response(
                {"detail": "`agent` query param is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        period = request.query_params.get("period", "monthly")
        from core.utils.dates import get_period_range
        try:
            start, end = get_period_range(period)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            RouteReportingService.agent_performance(int(agent_id), start, end)
        )