from rest_framework import serializers

from ..models import PrintJob


class PrintJobListSerializer(serializers.ModelSerializer):
    printer_name = serializers.CharField(source="printer.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    document_type_display = serializers.CharField(
        source="get_document_type_display", read_only=True,
    )
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PrintJob
        fields = (
            "id", "printer", "printer_name",
            "document_type", "document_type_display",
            "reference_type", "reference_id",
            "status", "status_display",
            "attempts", "error_message",
            "created_by", "created_by_name",
            "created_at", "printed_at",
        )

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        u = obj.created_by
        return u.get_full_name() or u.username


class PrintJobDetailSerializer(PrintJobListSerializer):
    payload = serializers.JSONField(read_only=True)
    escpos_base64 = serializers.CharField(read_only=True)

    class Meta(PrintJobListSerializer.Meta):
        fields = PrintJobListSerializer.Meta.fields + (
            "payload", "escpos_base64", "last_attempt_at",
        )


class PrintJobCreateSerializer(serializers.Serializer):
    printer = serializers.IntegerField(required=False, allow_null=True)
    document_type = serializers.ChoiceField(choices=PrintJob.DocumentType.choices)
    reference_type = serializers.CharField(required=False, allow_blank=True)
    reference_id = serializers.CharField(required=False, allow_blank=True)
    payload = serializers.JSONField(required=False, default=dict)


class QueueReceiptSerializer(serializers.Serializer):
    sale = serializers.IntegerField()


class QueueCreditNoteSerializer(serializers.Serializer):
    sales_return = serializers.IntegerField()


class QueuePreorderSlipSerializer(serializers.Serializer):
    preorder = serializers.IntegerField()


class QueueRouteSheetSerializer(serializers.Serializer):
    run = serializers.IntegerField()


class PushResultSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    error = serializers.CharField(required=False, allow_blank=True)