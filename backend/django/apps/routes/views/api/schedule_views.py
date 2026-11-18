from django_filters import rest_framework as django_filters
from rest_framework import viewsets

from apps.routes.models import RouteSchedule
from apps.routes.permissions import CanManageRoutes
from apps.routes.serializers import RouteScheduleSerializer


class ScheduleFilterSet(django_filters.FilterSet):
    route = django_filters.NumberFilter()
    day_of_week = django_filters.NumberFilter()

    class Meta:
        model = RouteSchedule
        fields = ("route", "day_of_week")


class RouteScheduleViewSet(viewsets.ModelViewSet):
    queryset = RouteSchedule.objects.select_related("route").all().order_by("route__code", "day_of_week")
    serializer_class = RouteScheduleSerializer
    permission_classes = [CanManageRoutes]
    pagination_class = None
    filterset_class = ScheduleFilterSet