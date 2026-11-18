from django.contrib import admin

from .models import Route, RouteChangeLog, RouteRun, RouteSchedule


class RouteScheduleInline(admin.TabularInline):
    model = RouteSchedule
    extra = 0


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "default_agent", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")
    inlines = [RouteScheduleInline]


@admin.register(RouteSchedule)
class RouteScheduleAdmin(admin.ModelAdmin):
    list_display = ("route", "day_of_week", "is_active")
    list_filter = ("day_of_week", "is_active")
    list_select_related = ("route",)


@admin.register(RouteRun)
class RouteRunAdmin(admin.ModelAdmin):
    list_display = (
        "id", "route", "agent", "stock_location", "run_date",
        "status", "cash_collected", "cash_variance",
    )
    list_filter = ("status", "route")
    search_fields = ("route__code", "route__name", "agent__username")
    list_select_related = ("route", "agent", "stock_location")
    readonly_fields = (
        "opening_stock_value", "closing_stock_value",
        "cash_collected", "cash_expected", "cash_handed_in", "cash_variance",
        "started_at", "completed_at",
    )


@admin.register(RouteChangeLog)
class RouteChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "route", "change_type", "previous_agent", "new_agent",
        "changed_by", "changed_at",
    )
    list_filter = ("change_type", "route")
    search_fields = ("route__code", "route__name", "reason")
    list_select_related = ("route", "previous_agent", "new_agent", "changed_by")
    readonly_fields = [f.name for f in RouteChangeLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False