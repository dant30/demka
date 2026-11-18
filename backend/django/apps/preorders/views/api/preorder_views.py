from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from apps.common.pagination import StandardPagination
from apps.preorders.authentication import PreorderSessionAuthentication
from apps.preorders.permissions import IsPortalCustomer
from apps.preorders.serializers import (
    CancelPreorderSerializer,
    PreorderDetailSerializer,
    PreorderListSerializer,
    PreorderSubmitSerializer,
)
from apps.preorders.services import PreorderService


class MyOrdersViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    """Customer-facing: only the authenticated customer's own preorders."""

    authentication_classes = [PreorderSessionAuthentication]
    permission_classes = [IsPortalCustomer]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            self.request.user.customer.preorders
            .select_related("converted_sale")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return PreorderListSerializer
        if self.action == "create":
            return PreorderSubmitSerializer
        if self.action == "cancel":
            return CancelPreorderSerializer
        return PreorderDetailSerializer

    def create(self, request, *args, **kwargs):
        s = PreorderSubmitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        preorder = PreorderService.submit(request.user.customer, s.validated_data)
        return Response(
            PreorderDetailSerializer(preorder).data,
            status=status.HTTP_201_CREATED,
        )

    def cancel(self, request, pk=None):
        preorder = self.get_object()
        s = CancelPreorderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        preorder = PreorderService.cancel(
            preorder.pk, None, s.validated_data.get("reason", ""), by_customer=True,
        )
        return Response(PreorderDetailSerializer(preorder).data)