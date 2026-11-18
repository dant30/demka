"""Scoped throttles."""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class OtpRateThrottle(AnonRateThrottle):
    scope = "otp"


class FieldSyncThrottle(UserRateThrottle):
    scope = "field_sync"