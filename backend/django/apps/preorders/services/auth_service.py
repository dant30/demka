"""
Portal auth — OTP issuance and verification.

Security rules:
    * OTP is hashed with Django's password hasher, never stored plaintext.
    * Per-phone limit: 5 OTP requests / hour (silent — returns "sent" regardless).
    * Per-session limit: 5 wrong guesses invalidates the session.
    * Customer must be RESELLER + active; wrong/existing phones get identical responses.
"""
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.utils import timezone

from core.exceptions.domain import ValidationError
from core.services.sms import SmsError, SmsService
from core.utils.validators import validate_kenyan_phone

from ..models import PreorderCustomerSession


OTP_TTL = timedelta(minutes=5)
OTP_LENGTH = 6
PHONE_RATE_WINDOW = 60 * 60
PHONE_RATE_LIMIT = 5
MAX_VERIFY_ATTEMPTS = 5


class PortalAuthService:

    @staticmethod
    def _phone_rate_ok(phone: str) -> bool:
        key = f"preorder_otp_count:{phone}"
        count = cache.get(key, 0)
        if count >= PHONE_RATE_LIMIT:
            return False
        cache.set(key, count + 1, timeout=PHONE_RATE_WINDOW)
        return True

    @classmethod
    def request_otp(cls, phone: str, *, ip=None, user_agent="") -> dict:
        """
        Always returns the same body — never leaks customer existence or
        whether rate limits were hit.
        """
        try:
            validate_kenyan_phone(phone)
        except ValidationError:
            # Deliberately generic response.
            return {"detail": "If the phone is registered, an OTP has been sent."}

        if not cls._phone_rate_ok(phone):
            return {"detail": "If the phone is registered, an OTP has been sent."}

        from apps.customers.models import Customer
        customer = Customer.objects.filter(
            phone=phone, is_active=True, customer_type="RESELLER",
        ).first()
        if not customer:
            return {"detail": "If the phone is registered, an OTP has been sent."}

        otp = "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))
        token = secrets.token_urlsafe(32)

        PreorderCustomerSession.objects.create(
            customer=customer,
            otp_code=make_password(otp),
            otp_expires_at=timezone.now() + OTP_TTL,
            session_token=token,
            is_active=False,
            ip_address=ip,
            user_agent=user_agent[:300],
        )

        try:
            SmsService.send(
                phone,
                f"Your DEMKA portal verification code is {otp}. "
                f"Valid for 5 minutes. Do not share.",
            )
        except SmsError:
            # Never leak SMS failures to the caller.
            pass

        return {"detail": "If the phone is registered, an OTP has been sent."}

    @classmethod
    def verify_otp(cls, phone: str, otp: str, *, ip=None, user_agent="") -> dict:
        from apps.customers.models import Customer

        customer = Customer.objects.filter(
            phone=phone, is_active=True, customer_type="RESELLER",
        ).first()
        if not customer:
            raise ValidationError("Invalid phone or OTP.")

        session = (
            PreorderCustomerSession.objects
            .filter(
                customer=customer,
                is_active=False,
                used_at__isnull=True,
                otp_expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )
        if not session:
            raise ValidationError("Invalid or expired OTP.")
        if session.attempts >= MAX_VERIFY_ATTEMPTS:
            raise ValidationError("Too many failed attempts. Request a new code.")

        if not check_password(otp, session.otp_code):
            session.attempts += 1
            if session.attempts >= MAX_VERIFY_ATTEMPTS:
                session.used_at = timezone.now()
                session.save(update_fields=["attempts", "used_at"])
                raise ValidationError("Too many failed attempts. Request a new code.")
            session.save(update_fields=["attempts"])
            raise ValidationError("Invalid OTP.")

        session.is_active = True
        session.verified_at = timezone.now()
        session.save(update_fields=["is_active", "verified_at"])

        return {
            "session_token": session.session_token,
            "expires_at": (session.verified_at + timedelta(hours=24)).isoformat(),
            "customer": {
                "id": customer.pk,
                "code": customer.code,
                "name": customer.name,
                "phone": customer.phone,
                "credit_limit": str(customer.credit_limit),
                "current_balance": str(customer.current_balance),
            },
        }

    @staticmethod
    def logout(session) -> None:
        if session and session.is_active:
            session.is_active = False
            session.used_at = timezone.now()
            session.save(update_fields=["is_active", "used_at"])