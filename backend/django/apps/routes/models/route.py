from django.db import models


class Route(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    default_agent = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class RouteSchedule(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.PositiveSmallIntegerField()  # 0=Mon .. 6=Sun
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["route", "day_of_week"], name="uniq_route_day",
            ),
        ]


class RouteRun(models.Model):
    class Status(models.TextChoices):
        PLANNED     = "PLANNED",     "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED   = "COMPLETED",   "Completed"
        CANCELLED   = "CANCELLED",   "Cancelled"

    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="runs")
    agent = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    stock_location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)
    run_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    opening_stock_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_stock_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    # Reconciliation snapshots — set at start/complete, never edited after
    cash_expected = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    cash_handed_in = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    cash_variance = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )

    started_by = models.ForeignKey(
        "accounts.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="route_runs_started",
    )
    completed_by = models.ForeignKey(
        "accounts.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="route_runs_completed",
    )

    class Meta:
        ordering = ["-run_date", "-id"]
        indexes = [
            models.Index(fields=["route", "run_date"]),
            models.Index(fields=["agent", "run_date"]),
            models.Index(fields=["status", "run_date"]),
        ]


class RouteChangeLog(models.Model):
    class ChangeType(models.TextChoices):
            REASSIGN_CUSTOMER = "REASSIGN_CUSTOMER", "Reassign Customer"
            REASSIGN_AGENT = "REASSIGN_AGENT", "Reassign Agent"
            ROUTE_MERGE = "ROUTE_MERGE", "Route Merge"
            ROUTE_SPLIT = "ROUTE_SPLIT", "Route Split"
            DEACTIVATE = "DEACTIVATE", "Deactivate"

    route = models.ForeignKey(Route, on_delete=models.PROTECT)
    change_type = models.CharField(max_length=30, choices=ChangeType.choices)
    affected_customers = models.JSONField(default=list, blank=True)
    previous_agent = models.ForeignKey("accounts.User", null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name="route_changes_from")
    new_agent = models.ForeignKey("accounts.User", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="route_changes_to")
    reason = models.TextField()
    changed_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="route_changes_made")
    changed_at = models.DateTimeField(auto_now_add=True)