from rest_framework.routers import DefaultRouter

from apps.customers.views.api import (
    CustomerContactViewSet,
    CustomerRouteAssignmentViewSet,
    CustomerViewSet,
)


router = DefaultRouter()
router.register("contacts", CustomerContactViewSet, basename="customer-contact")
router.register(
    "route-assignments",
    CustomerRouteAssignmentViewSet,
    basename="customer-route-assignment",
)
router.register("", CustomerViewSet, basename="customer")

urlpatterns = router.urls