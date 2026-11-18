from rest_framework.routers import DefaultRouter

from apps.routes.views.api import (
    RouteChangeLogViewSet,
    RouteRunViewSet,
    RouteScheduleViewSet,
    RouteViewSet,
)


router = DefaultRouter()
router.register("schedules", RouteScheduleViewSet, basename="route-schedule")
router.register("runs", RouteRunViewSet, basename="route-run")
router.register("change-log", RouteChangeLogViewSet, basename="route-change-log")
router.register("", RouteViewSet, basename="route")

urlpatterns = router.urls