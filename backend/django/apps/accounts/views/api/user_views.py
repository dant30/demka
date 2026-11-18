from django.contrib.auth import get_user_model
from django_filters import rest_framework as django_filters
from rest_framework import filters, viewsets

from apps.accounts.permissions import IsBossOnly
from apps.accounts.serializers.user import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination


User = get_user_model()


class UserFilterSet(django_filters.FilterSet):
    role = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = User
        fields = ("role", "is_active")


class UserViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsBossOnly]
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = UserFilterSet
    search_fields = ("username", "first_name", "last_name", "phone", "email")
    ordering_fields = ("created_at", "username", "role")
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer