from django.db.models import Q
from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.inventory.models import StockLocation, StockTransfer
from apps.inventory.permissions import CanInitiateTransfer
from apps.inventory.serializers import (
    StockTransferCreateSerializer,
    StockTransferDetailSerializer,
    StockTransferListSerializer,
)
from apps.inventory.services import TransferService


class StockTransferFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    from_location = django_filters.NumberFilter()
    to_location = django_filters.NumberFilter()

    class Meta:
        model = StockTransfer
        fields = ("status", "from_location", "to_location")


class StockTransferViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        StockTransfer.objects
        .select_related("from_location", "to_location", "initiated_by", "received_by")
        .prefetch_related("items__product")
        .all()
    )
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_class = StockTransferFilterSet
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options"]  # lifecycle via actions

    def get_permissions(self):
        return [CanInitiateTransfer()]

    def get_serializer_class(self):
        if self.action == "list":
            return StockTransferListSerializer
        if self.action == "create":
            return StockTransferCreateSerializer
        return StockTransferDetailSerializer

    def create(self, request, *args, **kwargs):
        s = StockTransferCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        from_loc = StockLocation.objects.filter(pk=s.validated_data["from_location"]).first()
        to_loc = StockLocation.objects.filter(pk=s.validated_data["to_location"]).first()
        if not from_loc or not to_loc:
            return Response(
                {"detail": "Source or destination location not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if getattr(request.user, "role", None) == "FIELD_AGENT":
            allowed_ids = set(
                StockLocation.objects.filter(
                    pk__in=(from_loc.pk, to_loc.pk),
                    is_active=True,
                ).filter(
                    Q(assigned_agent=request.user)
                    | Q(location_type=StockLocation.Type.SHOP)
                ).values_list("pk", flat=True)
            )
            if allowed_ids != {from_loc.pk, to_loc.pk}:
                return Response(
                    {"detail": "Field agents can transfer only between their assigned location and a shop."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        transfer = TransferService.create(
            from_location=from_loc,
            to_location=to_loc,
            items=s.validated_data["items"],
            user=request.user,
            notes=s.validated_data.get("notes", ""),
        )
        return Response(
            StockTransferDetailSerializer(transfer).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch_transfer(self, request, pk=None):
        transfer = TransferService.dispatch(int(pk), request.user)
        return Response(StockTransferDetailSerializer(transfer).data)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive_transfer(self, request, pk=None):
        transfer = TransferService.receive(int(pk), request.user)
        return Response(StockTransferDetailSerializer(transfer).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_transfer(self, request, pk=None):
        transfer = TransferService.cancel(int(pk), request.user)
        return Response(StockTransferDetailSerializer(transfer).data)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == "FIELD_AGENT":
            qs = qs.filter(
                from_location__assigned_agent=user
            ) | qs.filter(to_location__assigned_agent=user)
        return qs.distinct()