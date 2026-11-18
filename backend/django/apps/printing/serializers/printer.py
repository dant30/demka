from rest_framework import serializers

from ..models import Printer


class PrinterSerializer(serializers.ModelSerializer):
    printer_type_display = serializers.CharField(
        source="get_printer_type_display", read_only=True,
    )
    assigned_location_name = serializers.CharField(
        source="assigned_location.name", read_only=True, default=None,
    )
    assigned_user_name = serializers.SerializerMethodField()
    transport_summary = serializers.CharField(read_only=True)
    queued_jobs = serializers.SerializerMethodField()
    last_printed_at = serializers.SerializerMethodField()

    class Meta:
        model = Printer
        fields = (
            "id", "name", "printer_type", "printer_type_display",
            "identifier",
            "ip_address", "port",
            "usb_vendor_id", "usb_product_id",
            "bt_mac_address", "bt_rfcomm_channel",
            "assigned_location", "assigned_location_name",
            "assigned_user", "assigned_user_name",
            "paper_width_mm", "supports_cash_drawer", "is_default", "is_active",
            "transport_summary", "queued_jobs", "last_printed_at",
            "notes", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_assigned_user_name(self, obj):
        if not obj.assigned_user:
            return None
        u = obj.assigned_user
        return u.get_full_name() or u.username

    def get_queued_jobs(self, obj):
        from ..models import PrintJob
        return obj.jobs.filter(status=PrintJob.Status.QUEUED).count()

    def get_last_printed_at(self, obj):
        from ..models import PrintJob
        last = obj.jobs.filter(status=PrintJob.Status.PRINTED).order_by("-printed_at").first()
        return last.printed_at.isoformat() if last and last.printed_at else None


class PrinterWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Printer
        fields = (
            "name", "printer_type", "identifier",
            "ip_address", "port",
            "usb_vendor_id", "usb_product_id",
            "bt_mac_address", "bt_rfcomm_channel",
            "assigned_location", "assigned_user",
            "paper_width_mm", "supports_cash_drawer", "is_default", "is_active",
            "notes",
        )

    def validate(self, attrs):
        ptype = attrs.get("printer_type") or (self.instance.printer_type if self.instance else None)
        if ptype == Printer.Type.NETWORK and not attrs.get("ip_address") and not getattr(self.instance, "ip_address", None):
            raise serializers.ValidationError(
                {"ip_address": "Required for NETWORK printers."}
            )
        if ptype == Printer.Type.USB:
            vid = attrs.get("usb_vendor_id") or getattr(self.instance, "usb_vendor_id", "")
            pid = attrs.get("usb_product_id") or getattr(self.instance, "usb_product_id", "")
            if not vid or not pid:
                raise serializers.ValidationError(
                    {"usb_vendor_id": "Vendor and product IDs required for USB printers."}
                )
        if ptype == Printer.Type.BLUETOOTH and not attrs.get("identifier") and not getattr(self.instance, "identifier", ""):
            raise serializers.ValidationError(
                {"identifier": "OS serial path required for Bluetooth (e.g. /dev/rfcomm0 or COM4)."}
            )
        return attrs