"""Common filtersets."""
from django_filters import rest_framework as filters


class DateRangeFilterSet(filters.FilterSet):
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    updated_after = filters.DateTimeFilter(field_name="updated_at", lookup_expr="gte")
    updated_before = filters.DateTimeFilter(field_name="updated_at", lookup_expr="lte")


class ActiveFilterSet(filters.FilterSet):
    is_active = filters.BooleanFilter()