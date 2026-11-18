from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    REQUIRED_FIELDS = ["email", "phone"]

    class Role(models.TextChoices):
        ADMIN        = "ADMIN",        "Admin"
        BOSS         = "BOSS",         "Boss"
        SALES_HELPER = "SALES_HELPER", "Sales Helper"
        FIELD_AGENT  = "FIELD_AGENT",  "Field Agent"

    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SALES_HELPER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserLocationAssignment(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="location_assignments"
    )
    location = models.ForeignKey(
        "inventory.StockLocation", on_delete=models.CASCADE
    )
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "location"], name="uniq_user_location"
            ),
        ]

    def __str__(self):
        return f"{self.user.username} @ {self.location.name}"


class AuditLog(models.Model):
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name}#{self.object_id}"