"""
Portal authentication — opaque session tokens.

Session lifecycle:
    Request OTP → session (inactive) with hashed OTP, 5-min TTL
    Verify OTP  → session.is_active=True, verified_at=now, 24h TTL
    Every request → session.verified_at + 24h > now; else 401
    Logout       → session.is_active=False
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import PreorderCustomerSession


SESSION_LIFETIME = timedelta(hours=24)


class PortalUser:
    """Proxy that satisfies DRF's `is_authenticated` contract without being a Django User."""

    is_authenticated = True
    is_anonymous = False
    role = "PORTAL_CUSTOMER"

    def __init__(self, customer, session):
        self.customer = customer
        self.session = session
        self.id = customer.id
        self.pk = customer.id
        self.username = customer.phone
        self.phone = customer.phone
        self.name = customer.name
        self.customer_type = customer.customer_type


class PreorderSessionAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.lower().startswith(self.keyword.lower() + " "):
            return None
        token = header.split(" ", 1)[1].strip()
        if not token:
            return None

        session = (
            PreorderCustomerSession.objects
            .select_related("customer")
            .filter(
                session_token=token,
                is_active=True,
                verified_at__isnull=False,
            )
            .first()
        )
        if not session:
            raise AuthenticationFailed("Invalid or expired session.")

        if session.verified_at + SESSION_LIFETIME < timezone.now():
            session.is_active = False
            session.save(update_fields=["is_active"])
            raise AuthenticationFailed("Session expired.")

        customer = session.customer
        if not customer.is_active:
            raise AuthenticationFailed("Account inactive.")
        if customer.customer_type != "RESELLER":
            raise AuthenticationFailed("Portal access is for resellers only.")

        session.save(update_fields=["last_activity_at"])
        return (PortalUser(customer, session), session)
    