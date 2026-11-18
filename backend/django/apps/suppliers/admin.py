from django.contrib import admin
from .models import Supplier, SupplierProduct


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
	search_fields = ("code", "name", "phone", "email")


admin.site.register(SupplierProduct)
