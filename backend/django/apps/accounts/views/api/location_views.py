from rest_framework import viewsets

from apps.accounts.models import UserLocationAssignment
from apps.accounts.permissions import IsBossOrSelf
from apps.accounts.serializers.location import UserLocationAssignmentSerializer
from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination


class UserLocationAssignmentViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = UserLocationAssignment.objects.select_related("user", "location").all()
    serializer_class = UserLocationAssignmentSerializer
    permission_classes = [IsBossOrSelf]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self.request.user, "role", None) not in ("BOSS", "ADMIN"):
            qs = qs.filter(user=self.request.user)
        return qs