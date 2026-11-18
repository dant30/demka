"""Phone-based OTP for preorder portal and field customers."""
import secrets
from django.core.cache import cache

OTP_TTL_SECONDS = 300
OTP_LENGTH = 6


def generate_otp(phone: str) -> str:
    otp = "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))
    cache.set(f"otp:{phone}", otp, timeout=OTP_TTL_SECONDS)
    return otp


def verify_otp(phone: str, otp: str) -> bool:
    stored = cache.get(f"otp:{phone}")
    if stored and stored == otp:
        cache.delete(f"otp:{phone}")
        return True
    return False