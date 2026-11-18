"""Audit service — writes to apps.accounts.AuditLog."""
from typing import Optional


def log(user, action: str, instance, changes: Optional[dict] = None,
        ip_address: Optional[str] = None) -> None:
    from django.contrib.auth import get_user_model
    from apps.accounts.models import AuditLog

    valid_user = user if isinstance(user, get_user_model()) else None
    AuditLog.objects.create(
        user=valid_user,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=str(getattr(instance, "pk", "")),
        changes=changes or {},
        ip_address=ip_address,
    )


def diff(before: dict, after: dict) -> dict:
    keys = set(before) | set(after)
    return {
        k: {"before": before.get(k), "after": after.get(k)}
        for k in keys if before.get(k) != after.get(k)
    }


def model_snapshot(instance, fields: list[str]) -> dict:
    return {f: str(getattr(instance, f, None)) for f in fields}