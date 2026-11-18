from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.etims.models import EtimsConfig
from apps.etims.permissions import CanManageEtimsConfig, CanViewEtims
from apps.etims.serializers import EtimsConfigSerializer, EtimsConfigWriteSerializer
from apps.etims.services.client import EtimsClient, EtimsError
from apps.etims.services import ETIMSService


class EtimsConfigView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [CanViewEtims()]
        return [CanManageEtimsConfig()]

    @extend_schema(responses=EtimsConfigSerializer)
    def get(self, request):
        return Response(EtimsConfigSerializer(EtimsConfig.get_solo()).data)

    @extend_schema(request=EtimsConfigWriteSerializer, responses=EtimsConfigSerializer)
    def patch(self, request):
        cfg = EtimsConfig.get_solo()
        s = EtimsConfigWriteSerializer(cfg, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(EtimsConfigSerializer(EtimsConfig.get_solo()).data)

    def post(self, request):
        """Initialise the device with KRA and persist the cmcKey."""
        cfg = EtimsConfig.get_solo()
        try:
            client = EtimsClient(cfg)
            info = client.initialize_device()
        except EtimsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from django.utils import timezone
        cfg.cmc_key = info.get("cmcKey", "")
        cfg.sdc_id = info.get("sdcId", "")
        cfg.mrc_no = info.get("mrcNo", "")
        cfg.trade_name = info.get("tradeNm", "")
        cfg.branch_name = info.get("bhfNm", "")
        cfg.initialized_at = timezone.now()
        cfg.save()
        return Response(EtimsConfigSerializer(cfg).data)