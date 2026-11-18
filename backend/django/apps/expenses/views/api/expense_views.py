from datetime import date

from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import LargePagination
from apps.expenses.models import Expense
from apps.expenses.permissions import (
    CanCreateExpense,
    CanManageExpenses,
    CanViewExpenses,
)
from apps.expenses.serializers import (
    ExpenseCreateSerializer,
    ExpenseDetailSerializer,
    ExpenseListSerializer,
    ExpenseUpdateSerializer,
)
from apps.expenses.services import ExpenseService
from core.utils.dates import get_period_range


class ExpenseFilterSet(django_filters.FilterSet):
    category = django_filters.NumberFilter()
    payment_method = django_filters.NumberFilter()
    location = django_filters.NumberFilter()
    route_run = django_filters.NumberFilter()
    paid_by = django_filters.NumberFilter()
    date_after = django_filters.DateFilter(field_name="expense_date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="expense_date", lookup_expr="lte")
    has_receipt = django_filters.BooleanFilter(method="filter_has_receipt")

    class Meta:
        model = Expense
        fields = ("category", "payment_method", "location", "route_run", "paid_by")

    def filter_has_receipt(self, queryset, name, value):
        if value:
            return queryset.exclude(receipt_image="")
        return queryset.filter(receipt_image="")


class ExpenseViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        Expense.objects
        .select_related("category", "payment_method", "location", "route_run__route", "paid_by")
        .all()
    )
    pagination_class = LargePagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ExpenseFilterSet
    search_fields = ("expense_number", "description", "reference", "category__name")
    ordering_fields = ("expense_date", "amount", "created_at")
    ordering = ["-expense_date", "-created_at"]

    def get_permissions(self):
        if self.action == "create":
            return [CanCreateExpense()]
        if self.action in ("update", "partial_update", "destroy"):
            return [CanManageExpenses()]
        return [CanViewExpenses()]

    def get_serializer_class(self):
        if self.action == "list":
            return ExpenseListSerializer
        if self.action == "create":
            return ExpenseCreateSerializer
        if self.action in ("update", "partial_update"):
            return ExpenseUpdateSerializer
        return ExpenseDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, "role", None)
        if role in ("SALES_HELPER", "FIELD_AGENT"):
            # Non-boss: only expenses they personally paid/recorded
            qs = qs.filter(paid_by=user)
        return qs

    # ---- Override create / update to use service --------
    def create(self, request, *args, **kwargs):
        s = ExpenseCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        expense = ExpenseService.create(s.validated_data, request.user)
        return Response(
            ExpenseDetailSerializer(expense, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        s = ExpenseUpdateSerializer(data=request.data, partial=partial)
        s.is_valid(raise_exception=True)
        expense = ExpenseService.update(instance.pk, s.validated_data, request.user)
        return Response(
            ExpenseDetailSerializer(expense, context={"request": request}).data,
        )

    # ---- Summary actions --------------------------------
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        period = request.query_params.get("period", "monthly")
        try:
            start, end = get_period_range(period)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # optional anchors
        if request.query_params.get("start"):
            start = date.fromisoformat(request.query_params["start"])
        if request.query_params.get("end"):
            end = date.fromisoformat(request.query_params["end"])

        return Response(ExpenseService.summary(start, end))

    @action(detail=False, methods=["get"], url_path="by-category")
    def by_category(self, request):
        start, end = self._parse_range(request)
        return Response(ExpenseService.by_category(start, end))

    @action(detail=False, methods=["get"], url_path="by-location")
    def by_location(self, request):
        start, end = self._parse_range(request)
        return Response(ExpenseService.by_location(start, end))

    @action(detail=False, methods=["get"], url_path="monthly-trend")
    def monthly_trend(self, request):
        try:
            months = int(request.query_params.get("months", 6))
        except ValueError:
            months = 6
        months = max(1, min(24, months))
        return Response(ExpenseService.monthly_trend(months))

    @action(detail=False, methods=["get"], url_path="by-route-run/(?P<run_id>[^/.]+)")
    def by_route_run(self, request, run_id=None):
        return Response(ExpenseService.by_route_run(int(run_id)))

    # ---- Helpers ---------------------------------------
    def _parse_range(self, request):
        period = request.query_params.get("period", "monthly")
        try:
            start, end = get_period_range(period)
        except ValueError as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(exc))
        if request.query_params.get("start"):
            start = date.fromisoformat(request.query_params["start"])
        if request.query_params.get("end"):
            end = date.fromisoformat(request.query_params["end"])
        return start, end