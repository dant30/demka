from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.inventory.views.api import (
    CategoryViewSet,
    ProductImportView,
    ProductTemplateView,
    ProductViewSet,
    StockAdjustView,
    StockLevelViewSet,
    StockLocationViewSet,
    StockMovementViewSet,
    StockTransferViewSet,
)


router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("locations", StockLocationViewSet, basename="location")
router.register("stock-levels", StockLevelViewSet, basename="stock-level")
router.register("movements", StockMovementViewSet, basename="stock-movement")
router.register("transfers", StockTransferViewSet, basename="stock-transfer")

urlpatterns = [
    # Keep import paths ahead of the products/<pk>/ router patterns.
    path("products/import/template/", ProductTemplateView.as_view(), name="product-import-template"),
    path("products/import/", ProductImportView.as_view(), name="product-import"),
    path("stock/adjust/", StockAdjustView.as_view(), name="stock-adjust"),
] + router.urls