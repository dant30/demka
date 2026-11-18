from rest_framework import serializers

from ..models import EtimsSequence


class EtimsSequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtimsSequence
        fields = ("id", "tin", "bhf_id", "next_no")
        read_only_fields = fields