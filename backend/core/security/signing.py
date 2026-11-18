"""HMAC payload signing (webhooks, M-Pesa callbacks, etc.)."""
import hmac
import hashlib
import base64
from django.conf import settings


def sign_payload(payload: bytes) -> str:
    key = settings.SECRET_KEY.encode()
    digest = hmac.new(key, payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode()


def verify_signature(payload: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign_payload(payload), signature)