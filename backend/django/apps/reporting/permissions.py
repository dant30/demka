"""Reporting-specific DRF permissions."""
from rest_framework.permissions import BasePermission


BOSS_ROLES = ("BOSS", "ADMIN")


class CanViewReports(BasePermission):
	def has_permission(self, request, view):
		return (
			request.user is not None
			and request.user.is_authenticated
			and getattr(request.user, "role", None) in BOSS_ROLES
		)


class CanViewOwnMetricsOrBoss(BasePermission):
	"""Allow field agents through; the view must scope data to their own ID."""

	def has_permission(self, request, view):
		if not request.user or not request.user.is_authenticated:
			return False
		return getattr(request.user, "role", None) in (*BOSS_ROLES, "FIELD_AGENT")