from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.preorders.authentication import PreorderSessionAuthentication
from apps.preorders.permissions import IsPortalCustomer
from apps.preorders.serializers import RequestOTPSerializer, VerifyOTPSerializer
from apps.preorders.services import PortalAuthService


def _ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")


class RequestOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "portal_otp_request"

    @extend_schema(request=RequestOTPSerializer, responses={200: dict})
    def post(self, request):
        s = RequestOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = PortalAuthService.request_otp(
            s.validated_data["phone"],
            ip=_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
        return Response(result)


class VerifyOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "portal_otp_verify"

    @extend_schema(request=VerifyOTPSerializer, responses={200: dict})
    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = PortalAuthService.verify_otp(
            s.validated_data["phone"],
            s.validated_data["otp"],
            ip=_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
        )
        return Response(result, status=status.HTTP_200_OK)


class PortalLogoutView(APIView):
    authentication_classes = [PreorderSessionAuthentication]
    permission_classes = [IsPortalCustomer]

    def post(self, request):
        PortalAuthService.logout(request.auth)
        return Response(status=status.HTTP_204_NO_CONTENT)