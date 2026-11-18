from rest_framework import filters, viewsets

from apps.inventory.models import StockLocation
from apps.inventory.permissions import CanManageProducts
from apps.inventory.serializers import StockLocationSerializer


class StockLocationViewSet(viewsets.ModelViewSet):
    queryset = StockLocation.objects.select_related("assigned_agent").all()
    serializer_class = StockLocationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("name",)
    ordering = ["name"]

    def get_permissions(self):
        # same gating as products: read=any staff, write=boss
        return [CanManageProducts()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Field agents can only see their assigned location(s) + shop
        if getattr(user, "role", None) == "FIELD_AGENT":
            qs = qs.filter(assigned_agent=user)
        return qs