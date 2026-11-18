from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.customers.models import Customer
from apps.customers.permissions import (
    CanCreateCustomer,
    CanDeleteCustomer,
    CanViewCustomers,
)
from apps.customers.serializers import (
    AssignRouteSerializer,
    CustomerCreateSerializer,
    CustomerDetailSerializer,
    CustomerListSerializer,
    CustomerUpdateSerializer,
)
from apps.customers.services import CustomerService


class CustomerFilterSet(django_filters.FilterSet):
    customer_type = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()
    has_debt = django_filters.BooleanFilter(method="filter_has_debt")
    route = django_filters.NumberFilter(method="filter_route")

    class Meta:
        model = Customer
        fields = ("customer_type", "is_active")

    def filter_has_debt(self, queryset, name, value):
        if value:
            return queryset.filter(current_balance__gt=0)
        return queryset.filter(current_balance__lte=0)

    def filter_route(self, queryset, name, value):
        return queryset.filter(
            route_assignments__route_id=value,
            route_assignments__assigned_to__isnull=True,
        ).distinct()


class CustomerViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("created_by").all()
    permission_classes = [CanViewCustomers]
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CustomerFilterSet
    search_fields = ("code", "name", "phone", "email", "business_name")
    ordering_fields = ("created_at", "name", "current_balance", "code")
    ordering = ["name"]

    def get_permissions(self):
        if self.action == "create":
            return [CanCreateCustomer()]
        if self.action == "destroy":
            return [CanDeleteCustomer()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return CustomerListSerializer
        if self.action == "create":
            return CustomerCreateSerializer
        if self.action in ("update", "partial_update"):
            return CustomerUpdateSerializer
        return CustomerDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Field agents only see customers on their active routes
        if getattr(user, "role", None) == "FIELD_AGENT":
            qs = qs.filter(
                route_assignments__route__default_agent=user,
                route_assignments__assigned_to__isnull=True,
            ).distinct()
        return qs

    # ---- Custom actions -----------------------------------
    @action(detail=False, methods=["get"], url_path="walk-in")
    def walk_in(self, request):
        customer = CustomerService.get_or_create_walkin()
        return Response(CustomerListSerializer(customer).data)

    @action(detail=True, methods=["post"], url_path="assign-route")
    def assign_route(self, request, pk=None):
        customer = self.get_object()
        s = AssignRouteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        assignment = CustomerService.assign_route(
            customer_id=customer.pk,
            route_id=s.validated_data["route"],
            reason=s.validated_data.get("reason", ""),
            effective_date=s.validated_data.get("effective_date"),
        )
        return Response(
            {
                "assignment_id": assignment.pk,
                "customer": customer.pk,
                "route": assignment.route_id,
                "assigned_from": assignment.assigned_from,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="with-debt")
    def with_debt(self, request):
        qs = CustomerService.customers_with_debt()
        page = self.paginate_queryset(qs)
        data = CustomerListSerializer(page or qs, many=True).data
        return self.get_paginated_response(data) if page else Response(data)