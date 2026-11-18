from django.contrib import admin
from .models import DocumentSequence, TaxRate, BusinessConfiguration


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ("doc_type", "last_value")
    search_fields = ("doc_type",)


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "effective_from", "effective_to", "is_active")
    list_filter = ("is_active",)


@admin.register(BusinessConfiguration)
class BusinessConfigurationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not BusinessConfiguration.objects.exists()