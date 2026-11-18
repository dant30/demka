from decimal import Decimal

from rest_framework import serializers

from ..models import Expense


MAX_RECEIPT_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


class ExpenseListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    payment_method_code = serializers.CharField(source="payment_method.code", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True, default=None)
    route_run_display = serializers.SerializerMethodField()
    paid_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = (
            "id", "expense_number", "expense_date",
            "category", "category_name",
            "amount",
            "payment_method", "payment_method_code",
            "location", "location_name",
            "route_run", "route_run_display",
            "paid_by", "paid_by_name",
            "description",
            "created_at",
        )

    def get_route_run_display(self, obj):
        if not obj.route_run:
            return None
        run = obj.route_run
        return f"{run.route.name} ({run.run_date})" if run.route_id else f"Run #{run.pk}"

    def get_paid_by_name(self, obj):
        u = obj.paid_by
        return u.get_full_name() or u.username if u else None


class ExpenseDetailSerializer(ExpenseListSerializer):
    receipt_url = serializers.SerializerMethodField()

    class Meta(ExpenseListSerializer.Meta):
        fields = ExpenseListSerializer.Meta.fields + (
            "reference", "receipt_image", "receipt_url",
        )

    def get_receipt_url(self, obj):
        if not obj.receipt_image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.receipt_image.url)
        return obj.receipt_image.url


def _validate_receipt(file):
    if file is None:
        return file
    if file.size > MAX_RECEIPT_BYTES:
        raise serializers.ValidationError(
            f"Receipt image exceeds {MAX_RECEIPT_BYTES // (1024 * 1024)} MB."
        )
    content_type = getattr(file, "content_type", "")
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError(
            f"Unsupported image type: {content_type}."
        )
    return file


class ExpenseCreateSerializer(serializers.Serializer):
    category = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"),
    )
    description = serializers.CharField(required=False, allow_blank=True)
    expense_date = serializers.DateField()
    payment_method = serializers.IntegerField()
    reference = serializers.CharField(required=False, allow_blank=True, max_length=100)
    receipt_image = serializers.ImageField(required=False, allow_null=True)
    location = serializers.IntegerField(required=False, allow_null=True)
    route_run = serializers.IntegerField(required=False, allow_null=True)

    def validate_receipt_image(self, value):
        return _validate_receipt(value)


class ExpenseUpdateSerializer(serializers.Serializer):
    """Boss-only edit. All fields optional; immutable fields excluded."""

    category = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"),
        required=False,
    )
    description = serializers.CharField(required=False, allow_blank=True)
    expense_date = serializers.DateField(required=False)
    payment_method = serializers.IntegerField(required=False)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=100)
    receipt_image = serializers.ImageField(required=False, allow_null=True)
    location = serializers.IntegerField(required=False, allow_null=True)
    route_run = serializers.IntegerField(required=False, allow_null=True)

    def validate_receipt_image(self, value):
        return _validate_receipt(value)