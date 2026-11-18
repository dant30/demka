from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, viewsets

from apps.common.pagination import LargePagination
from apps.etims.models import EtimsItem
from apps.etims.permissions import CanViewEtims
from apps.etims.serializers import EtimsItemSerializer


class ItemFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()

    class Meta:
        model = EtimsItem
        fields = ("status",)


class EtimsItemViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    queryset = EtimsItem.objects.select_related("product").all()
    serializer_class = EtimsItemSerializer
    permission_classes = [CanViewEtims]
    pagination_class = LargePagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ItemFilterSet
    search_fields = ("item_cd", "item_cls_cd", "product__sku", "product__name")