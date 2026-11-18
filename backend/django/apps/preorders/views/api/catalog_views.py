from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Category
from apps.preorders.authentication import PreorderSessionAuthentication
from apps.preorders.permissions import IsPortalCustomer
from apps.preorders.serializers import CatalogCategorySerializer, CatalogProductSerializer
from apps.preorders.services import CatalogService
from core.utils.pagination import StandardPagination


class CatalogView(APIView):
    authentication_classes = [PreorderSessionAuthentication]
    permission_classes = [IsPortalCustomer]

    @extend_schema(responses=CatalogProductSerializer(many=True))
    def get(self, request):
        search = request.query_params.get("search", "").strip()
        category_id = request.query_params.get("category")
        only_in_stock = request.query_params.get("in_stock") == "true"

        qs = CatalogService.list_products(
            search=search,
            category_id=int(category_id) if category_id else None,
            only_in_stock=only_in_stock,
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        data = CatalogProductSerializer(page or qs, many=True, context={"request": request}).data
        if page is not None:
            return paginator.get_paginated_response(data)
        return Response(data)


class ProductDetailView(APIView):
    authentication_classes = [PreorderSessionAuthentication]
    permission_classes = [IsPortalCustomer]

    @extend_schema(responses=CatalogProductSerializer)
    def get(self, request, pk):
        product = CatalogService.get_product(int(pk))
        return Response(CatalogProductSerializer(product, context={"request": request}).data)


class CategoriesView(APIView):
    authentication_classes = [PreorderSessionAuthentication]
    permission_classes = [IsPortalCustomer]

    def get(self, request):
        qs = Category.objects.all().order_by("name")
        return Response(CatalogCategorySerializer(qs, many=True).data)