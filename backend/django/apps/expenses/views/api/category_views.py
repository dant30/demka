from rest_framework import filters, viewsets

from apps.common.mixins import AuditedViewSetMixin
from apps.expenses.models import ExpenseCategory
from apps.expenses.permissions import CanManageExpenseCategories
from apps.expenses.serializers import ExpenseCategorySerializer


class ExpenseCategoryViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = ExpenseCategory.objects.all().order_by("name")
    serializer_class = ExpenseCategorySerializer
    permission_classes = [CanManageExpenseCategories]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("name",)
    ordering = ["name"]