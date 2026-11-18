from rest_framework.routers import DefaultRouter

from apps.printing.views.api import PrinterViewSet, PrintJobViewSet


router = DefaultRouter()
router.register("printers", PrinterViewSet, basename="printer")
router.register("jobs", PrintJobViewSet, basename="print-job")

urlpatterns = router.urls