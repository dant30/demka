from rest_framework import viewsets

from apps.common.mixins import AuditedViewSetMixin
from apps.payments.models import PaymentMethod
from apps.payments.permissions import CanManagePaymentMethods
from apps.payments.serializers import PaymentMethodSerializer


class PaymentMethodViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all().order_by("name")
    serializer_class = PaymentMethodSerializer
    permission_classes = [CanManagePaymentMethods]
    pagination_class = None  # small list — no paging