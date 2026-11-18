# apps/common/services/numbering.py
from django.db import transaction

from apps.common.models import DocumentSequence


def next_number(doc_type: str, prefix: str = "", width: int = 6) -> str:
    with transaction.atomic():
        seq, _ = (
            DocumentSequence.objects
            .select_for_update()
            .get_or_create(doc_type=doc_type, defaults={"last_value": 0})
        )
        seq.last_value += 1
        seq.save(update_fields=["last_value"])
        n = str(seq.last_value).zfill(width)
        return f"{prefix}{n}" if prefix else n