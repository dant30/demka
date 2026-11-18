from rest_framework.routers import DefaultRouter

from apps.purchasing.views.api import (
    GoodsReceivedNoteViewSet,
    PurchaseOrderViewSet,
)


router = DefaultRouter()
router.register("purchase-orders", PurchaseOrderViewSet, basename="purchase-order")
router.register("grns", GoodsReceivedNoteViewSet, basename="grn")

urlpatterns = router.urls