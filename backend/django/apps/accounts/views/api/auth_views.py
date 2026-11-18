from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers.auth import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshSerializer,
    TokenPairSerializer,
)
from apps.accounts.serializers.user import MeSerializer
from apps.accounts.services import AuthService
from core.throttling.rates import LoginRateThrottle, OtpRateThrottle


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(request=LoginSerializer, responses={200: TokenPairSerializer})
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = AuthService.login(
            s.validated_data["identifier"],
            s.validated_data["password"],
        )
        return Response(result, status=status.HTTP_200_OK)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RefreshSerializer)
    def post(self, request):
        s = RefreshSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(AuthService.refresh(s.validated_data["refresh"]))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer)
    def post(self, request):
        s = LogoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        AuthService.logout(s.validated_data["refresh"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        return Response(MeSerializer(request.user).data)

    @extend_schema(request=MeSerializer, responses=MeSerializer)
    def patch(self, request):
        s = MeSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        AuthService.change_password(
            request.user,
            s.validated_data["current_password"],
            s.validated_data["new_password"],
        )
        return Response({"detail": "Password updated."})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    @extend_schema(request=PasswordResetRequestSerializer)
    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        AuthService.request_password_reset(s.validated_data["phone"])
        return Response(
            {"detail": "If the phone is registered, an OTP has been sent."}
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OtpRateThrottle]

    @extend_schema(request=PasswordResetConfirmSerializer)
    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        AuthService.confirm_password_reset(
            s.validated_data["phone"],
            s.validated_data["otp"],
            s.validated_data["new_password"],
        )
        return Response({"detail": "Password reset successful."})