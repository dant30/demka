from decimal import Decimal

from rest_framework import serializers

from ..models import Sale, SaleItem


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    returnable_quantity = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = SaleItem
        fields = (
            "id", "product", "product_name", "product_sku",
            "quantity", "unit_price", "unit_cost", "discount",
            "tax_rate", "line_total",
            "returned_quantity", "returnable_quantity",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or getattr(user, "role", None) not in ("BOSS", "ADMIN"):
            data.pop("unit_cost", None)
        return data


class SaleListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    sale_type_display = serializers.CharField(source="get_sale_type_display", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = (
            "id", "sale_number", "channel", "channel_display",
            "sale_type", "sale_type_display",
            "customer", "customer_name",
            "location",
            "agent", "agent_name",
            "status", "status_display",
            "total", "amount_paid", "balance_due", "is_credit_sale",
            "item_count",
            "created_at", "confirmed_at",
        )

    def get_agent_name(self, obj):
        if not obj.agent:
            return None
        return obj.agent.get_full_name() or obj.agent.username


class SaleDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    sale_type_display = serializers.CharField(source="get_sale_type_display", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    route_name = serializers.CharField(source="route.name", read_only=True, default=None)
    agent_name = serializers.SerializerMethodField()
    items = SaleItemSerializer(many=True, read_only=True)
    special_orders = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = (
            "id", "sale_number",
            "channel", "channel_display",
            "sale_type", "sale_type_display",
            "customer", "customer_name", "customer_phone",
            "location", "location_name",
            "route", "route_name",
            "agent", "agent_name",
            "status", "status_display",
            "subtotal", "discount_amount", "tax_amount", "total",
            "amount_paid", "balance_due", "is_credit_sale", "due_date",
            "notes",
            "etims_invoice_number", "etims_status",
            "created_at", "confirmed_at",
            "cancelled_at", "cancelled_by", "cancellation_reason",
            "items", "special_orders",
        )

    def get_agent_name(self, obj):
        if not obj.agent:
            return None
        return obj.agent.get_full_name() or obj.agent.username

    def get_special_orders(self, obj):
        from .special_order import SpecialOrderSerializer
        sos = [
            item.special_order
            for item in obj.items.select_related("special_order").all()
            if hasattr(item, "special_order")
        ]
        return SpecialOrderSerializer(sos, many=True).data


class _SaleLineWriteSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"),
        required=False, allow_null=True,
    )
    discount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
        required=False, default=Decimal("0"),
    )
    # Special-order extras (ignored when sale_type != SPECIAL_ORDER)
    supplier = serializers.IntegerField(required=False, allow_null=True)
    expected_arrival_date = serializers.DateField(required=False, allow_null=True)
    customer_deposit = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
        required=False, default=Decimal("0"),
    )


class SaleCreateSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=[("SHOP", "Shop"), ("FIELD", "Field")])
    sale_type = serializers.ChoiceField(
        choices=[("STANDARD", "Standard"), ("SPECIAL_ORDER", "Special Order")],
        default="STANDARD", required=False,
    )
    customer = serializers.IntegerField()
    location = serializers.IntegerField()
    route = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
        required=False, default=Decimal("0"),
    )
    amount_paid = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
        required=False, default=Decimal("0"),
    )
    payment_method = serializers.CharField(required=False, allow_blank=False)
    payment_reference = serializers.CharField(
        required=False, allow_blank=True, max_length=100,
    )
    items = _SaleLineWriteSerializer(many=True, allow_empty=False)
    confirm = serializers.BooleanField(default=True, required=False)


class SalePreviewSerializer(SaleCreateSerializer):
    confirm = serializers.BooleanField(default=False, required=False)


class SaleCancelSerializer(serializers.Serializer):
    reason = serializers.CharField()


class SalePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    method = serializers.CharField(help_text="PaymentMethod.code, e.g. CASH, MPESA, CREDIT")
    reference = serializers.CharField(required=False, allow_blank=True)
    mpesa_phone = serializers.CharField(required=False, allow_blank=True)
    mpesa_transaction_id = serializers.CharField(required=False, allow_blank=True)
    mpesa_receipt_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)