"""Reusable viewsets mixins."""
from apps.common.services.audit import log


class AuditedViewSetMixin:
    """Log create/update/delete into AuditLog."""
    audit_fields: list[str] = []

    def perform_create(self, serializer):
        instance = serializer.save()
        log(self.request.user, "CREATE", instance, ip_address=self._client_ip())
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        log(self.request.user, "UPDATE", instance, ip_address=self._client_ip())
        return instance

    def perform_destroy(self, instance):
        log(self.request.user, "DELETE", instance, ip_address=self._client_ip())
        instance.delete()

    def _client_ip(self):
        xff = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR")


class AgentScopedQuerysetMixin:
    """Restrict field-agent users to their own records."""
    agent_field = "agent"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == "FIELD_AGENT":
            return qs.filter(**{self.agent_field: user})
        return qs