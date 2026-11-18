from rest_framework import serializers

from ..models import CustomerLedgerEntry


class CustomerLedgerEntrySerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    entry_type_display = serializers.CharField(
        source="get_entry_type_display", read_only=True,
    )

    class Meta:
        model = CustomerLedgerEntry
        fields = (
            "id", "customer", "customer_name",
            "entry_type", "entry_type_display",
            "amount", "balance_after",
            "reference_type", "reference_id",
            "created_at",
        )
        read_only_fields = fields