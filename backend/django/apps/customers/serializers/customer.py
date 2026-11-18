from django.db import transaction
from rest_framework import serializers

from core.utils.validators import validate_kenyan_phone
from .contact import CustomerContactSerializer

from ..models import Customer, CustomerContact


def _phone_taken(value: str, exclude_pk=None) -> bool:
    qs = Customer.objects.filter(phone=value)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


class CustomerListSerializer(serializers.ModelSerializer):
    customer_type_display = serializers.CharField(
        source="get_customer_type_display", read_only=True
    )

    class Meta:
        model = Customer
        fields = (
            "id", "code", "name", "phone", "customer_type",
            "customer_type_display", "business_name",
            "credit_limit", "current_balance", "is_active",
        )


class CustomerDetailSerializer(serializers.ModelSerializer):
    customer_type_display = serializers.CharField(
        source="get_customer_type_display", read_only=True
    )
    contacts = serializers.SerializerMethodField()
    current_route = serializers.SerializerMethodField()
    ledger_summary = serializers.SerializerMethodField()
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id", "code", "name", "phone", "email",
            "customer_type", "customer_type_display",
            "business_name", "kra_pin", "physical_address",
            "credit_limit", "current_balance", "payment_terms_days",
            "is_active", "created_by", "created_by_display",
            "created_at", "updated_at",
            "contacts", "current_route", "ledger_summary",
        )

    def get_contacts(self, obj):
        return CustomerContactSerializer(
            obj.contacts.all(), many=True
        ).data

    def get_current_route(self, obj):
        assignment = (
            obj.route_assignments
            .filter(assigned_to__isnull=True)
            .select_related("route")
            .first()
        )
        if not assignment:
            return None
        return {
            "route_id": assignment.route_id,
            "route_code": assignment.route.code,
            "route_name": assignment.route.name,
            "assigned_from": assignment.assigned_from,
        }

    def get_ledger_summary(self, obj):
        from apps.payments.models import CustomerLedgerEntry

        entries = CustomerLedgerEntry.objects.filter(customer=obj)
        total_debits = sum(
            (entry.amount for entry in entries if entry.amount > 0), start=0,
        )
        total_credits = sum(
            (entry.amount for entry in entries if entry.amount < 0), start=0,
        )
        recent = list(
            entries.order_by("-created_at")[:5]
            .values("id", "entry_type", "amount", "balance_after", "created_at")
        )
        return {
            "total_invoiced": str(total_debits),
            "total_paid": str(abs(total_credits)),
            "current_balance": str(obj.current_balance),
            "recent_entries": recent,
        }

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username


class CustomerCreateSerializer(serializers.ModelSerializer):
    contacts = CustomerContactSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Customer
        fields = (
            "name", "phone", "email", "customer_type",
            "business_name", "kra_pin", "physical_address",
            "credit_limit", "payment_terms_days",
            "is_active", "contacts",
        )

    def validate_phone(self, value):
        validate_kenyan_phone(value)
        if _phone_taken(value):
            raise serializers.ValidationError(
                "A customer with this phone already exists."
            )
        return value

    def validate_kra_pin(self, value):
        if value and not value.upper().startswith("P"):
            # KRA PINs are often formatted P + 9 digits + letter
            # We only warn softly, do not block — legacy records vary
            pass
        return value.upper() if value else value

    def validate(self, attrs):
        user = self.context["request"].user
        if (
            "credit_limit" in attrs
            and attrs["credit_limit"] and attrs["credit_limit"] > 0
            and getattr(user, "role", None) not in ("BOSS", "ADMIN")
        ):
            raise serializers.ValidationError(
                {"credit_limit": "Only a boss can set a credit limit."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        contacts = validated_data.pop("contacts", [])
        user = self.context["request"].user
        customer = Customer.objects.create(created_by=user, **validated_data)
        for c in contacts:
            CustomerContact.objects.create(customer=customer, **c)
        return customer


class CustomerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "name", "phone", "email", "customer_type",
            "business_name", "kra_pin", "physical_address",
            "credit_limit", "payment_terms_days", "is_active",
        )

    def validate_phone(self, value):
        validate_kenyan_phone(value)
        if _phone_taken(value, exclude_pk=self.instance.pk if self.instance else None):
            raise serializers.ValidationError(
                "A customer with this phone already exists."
            )
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if (
            "credit_limit" in attrs
            and getattr(user, "role", None) not in ("BOSS", "ADMIN")
        ):
            raise serializers.ValidationError(
                {"credit_limit": "Only a boss can change a credit limit."}
            )
        return attrs


