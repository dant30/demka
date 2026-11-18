from rest_framework.routers import DefaultRouter

from apps.suppliers.views.api import (
    SupplierProductViewSet,
    SupplierViewSet,
)


router = DefaultRouter()
router.register("products", SupplierProductViewSet, basename="supplier-product")
router.register("", SupplierViewSet, basename="supplier")

urlpatterns = router.urls