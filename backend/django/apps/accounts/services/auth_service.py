"""Authentication services — login, refresh, logout, password workflows."""
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from core.authentication.otp import generate_otp, verify_otp
from core.exceptions.domain import NotFoundError, ValidationError
from core.services.sms import SmsError, SmsService


User = get_user_model()


class AuthService:

    @staticmethod
    def _user_snapshot(user) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "phone": user.phone,
            "role": user.role,
            "full_name": user.get_full_name() or user.username,
        }

    @classmethod
    def login(cls, identifier: str, password: str) -> dict:
        user = (
            User.objects.filter(username=identifier).first()
            or User.objects.filter(phone=identifier).first()
        )
        if user is None or not user.is_active or not user.check_password(password):
            raise ValidationError("Invalid credentials.")

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": cls._user_snapshot(user),
        }

    @staticmethod
    def refresh(refresh_token: str) -> dict:
        try:
            token = RefreshToken(refresh_token)
        except TokenError as exc:
            raise ValidationError(str(exc))
        return {"access": str(token.access_token)}

    @staticmethod
    def logout(refresh_token: str) -> None:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            # Already expired / blacklisted — ignore for idempotency
            pass

    @staticmethod
    def change_password(user, current_password: str, new_password: str) -> None:
        if not user.check_password(current_password):
            raise ValidationError({"current_password": "Incorrect current password."})
        user.set_password(new_password)
        user.save(update_fields=["password"])

    @staticmethod
    def request_password_reset(phone: str) -> None:
        # Silent success even if phone is unregistered — do not leak existence.
        if not User.objects.filter(phone=phone, is_active=True).exists():
            return
        otp = generate_otp(phone)
        try:
            SmsService.send(
                phone,
                f"Your DEMKA password reset OTP is {otp}. "
                f"It expires in 5 minutes. Do not share it.",
            )
        except SmsError:
            # Do not surface SMS provider failures to the caller.
            pass

    @staticmethod
    def confirm_password_reset(phone: str, otp: str, new_password: str) -> None:
        if not verify_otp(phone, otp):
            raise ValidationError({"otp": "Invalid or expired OTP."})
        user = User.objects.filter(phone=phone, is_active=True).first()
        if user is None:
            raise NotFoundError("User", phone)
        user.set_password(new_password)
        user.save(update_fields=["password"])