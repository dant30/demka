from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.routes.models import Route
from apps.routes.permissions import CanManageRoutes, CanViewRoutes
from apps.routes.serializers import (
    ChangeAgentSerializer,
    DeactivateRouteSerializer,
    ReassignCustomersSerializer,
    RouteDetailSerializer,
    RouteListSerializer,
    RouteWriteSerializer,
)
from apps.routes.services import RouteReportingService, RouteService
from core.utils.dates import get_period_range


class RouteFilterSet(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    default_agent = django_filters.NumberFilter()

    class Meta:
        model = Route
        fields = ("is_active", "default_agent")


class RouteViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = Route.objects.select_related("default_agent").all().order_by("code")
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = RouteFilterSet
    search_fields = ("code", "name", "description")
    ordering_fields = ("code", "name", "created_at")
    ordering = ["code"]

    def get_permissions(self):
        return [CanManageRoutes()]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action in ("create", "update", "partial_update"):
            return RouteWriteSerializer
        if self.action == "change_agent":
            return ChangeAgentSerializer
        if self.action == "reassign_customers":
            return ReassignCustomersSerializer
        if self.action == "deactivate":
            return DeactivateRouteSerializer
        return RouteDetailSerializer

    def create(self, request, *args, **kwargs):
        s = RouteWriteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        route = RouteService.create(s.validated_data, request.user)
        return Response(
            RouteDetailSerializer(route).data, status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        s = RouteWriteSerializer(data=request.data, partial=partial)
        s.is_valid(raise_exception=True)
        route = RouteService.update(instance.pk, s.validated_data, request.user)
        return Response(RouteDetailSerializer(route).data)

    # ---- Custom actions -----------------------------------
    @action(detail=True, methods=["post"], url_path="change-agent")
    def change_agent(self, request, pk=None):
        s = ChangeAgentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        route = RouteService.change_default_agent(
            int(pk),
            s.validated_data["new_agent"],
            request.user,
            s.validated_data["reason"],
        )
        return Response(RouteDetailSerializer(route).data)

    @action(detail=True, methods=["post"], url_path="reassign-customers")
    def reassign_customers(self, request, pk=None):
        s = ReassignCustomersSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = RouteService.reassign_customers(
            route_id=int(pk),
            customer_ids=s.validated_data["customer_ids"],
            target_route_id=s.validated_data["target_route"],
            user=request.user,
            reason=s.validated_data["reason"],
        )
        return Response(result)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        s = DeactivateRouteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        route = RouteService.deactivate(
            int(pk), request.user, s.validated_data["reason"],
        )
        return Response(RouteDetailSerializer(route).data)

    @action(detail=True, methods=["get"], url_path="profitability")
    def profitability(self, request, pk=None):
        period = request.query_params.get("period", "monthly")
        try:
            start, end = get_period_range(period)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RouteReportingService.route_profitability(int(pk), start, end))

    @action(detail=True, methods=["get"], url_path="runs")
    def runs(self, request, pk=None):
        from apps.routes.serializers import RouteRunListSerializer

        route = self.get_object()
        qs = route.runs.select_related("agent", "stock_location").order_by("-run_date")[:100]
        return Response(RouteRunListSerializer(qs, many=True).data)