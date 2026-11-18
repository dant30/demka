from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.payments.views.api import (
    CustomerLedgerEntryViewSet,
    MpesaCallbackView,
    MpesaSTKPushView,
    MpesaTransactionViewSet,
    PaymentMethodViewSet,
    PaymentViewSet,
)


router = DefaultRouter()
router.register("methods", PaymentMethodViewSet, basename="payment-method")
router.register("mpesa/transactions", MpesaTransactionViewSet, basename="mpesa-transaction")
router.register("ledger", CustomerLedgerEntryViewSet, basename="ledger")
router.register("", PaymentViewSet, basename="payment")

urlpatterns = [
    path("mpesa/stk-push/", MpesaSTKPushView.as_view(), name="mpesa-stk-push"),
    path("mpesa/callback/", MpesaCallbackView.as_view(), name="mpesa-callback"),
] + router.urls