from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views.api import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    AuditLogViewSet,
    UserLocationAssignmentViewSet,
    UserViewSet,
)


auth_patterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path(
        "password-reset/request/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
]

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register(
    "location-assignments",
    UserLocationAssignmentViewSet,
    basename="location-assignment",
)
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("auth/", include(auth_patterns)),
] + router.urls