from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.etims.views.api import (
    EtimsConfigView,
    EtimsInvoiceViewSet,
    EtimsItemViewSet,
    EtimsSequenceViewSet,
)


router = DefaultRouter()
router.register("invoices", EtimsInvoiceViewSet, basename="etims-invoice")
router.register("items", EtimsItemViewSet, basename="etims-item")
router.register("sequences", EtimsSequenceViewSet, basename="etims-sequence")

urlpatterns = [
    path("config/", EtimsConfigView.as_view(), name="etims-config"),
] + router.urls