from rest_framework.routers import DefaultRouter

from apps.sales.views.api import (
    SaleViewSet,
    SalesReturnViewSet,
    SpecialOrderViewSet,
)


router = DefaultRouter()
router.register("returns", SalesReturnViewSet, basename="sales-return")
router.register("special-orders", SpecialOrderViewSet, basename="special-order")
router.register("", SaleViewSet, basename="sale")

urlpatterns = router.urls