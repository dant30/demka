from rest_framework import filters, viewsets
from django_filters import rest_framework as django_filters

from apps.inventory.models import Category
from apps.inventory.permissions import CanManageProducts, CanViewInventory
from apps.inventory.serializers import CategorySerializer


class CategoryFilterSet(django_filters.FilterSet):
    applies_to = django_filters.CharFilter()
    parent = django_filters.NumberFilter()

    class Meta:
        model = Category
        fields = ("applies_to", "parent")


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related("parent").all()
    serializer_class = CategorySerializer
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CategoryFilterSet
    search_fields = ("name",)
    ordering_fields = ("name",)

    def get_permissions(self):
        return [CanManageProducts()]