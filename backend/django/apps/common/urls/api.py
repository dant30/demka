from django.urls import path
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from apps.common.models import BusinessConfiguration, TaxRate


class BusinessConfigurationView(RetrieveAPIView):
    def get(self, request):
        cfg = BusinessConfiguration.get_solo()
        return Response({
            "business_name": cfg.business_name,
            "kra_pin": cfg.kra_pin,
            "address": cfg.address,
            "phone": cfg.phone,
            "email": cfg.email,
            "receipt_footer": cfg.receipt_footer,
        })


class TaxRatesView(RetrieveAPIView):
    def get(self, request):
        rates = TaxRate.objects.filter(is_active=True).values("id", "name", "rate")
        return Response(list(rates))


urlpatterns = [
    path("config/", BusinessConfigurationView.as_view(), name="business-config"),
    path("tax-rates/", TaxRatesView.as_view(), name="tax-rates"),
]