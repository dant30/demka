"""Gap-free per-branch invcNo allocator. Row-locked."""
from django.db import transaction

from core.exceptions.domain import ValidationError

from ..models import EtimsSequence


class SequenceService:

    @staticmethod
    @transaction.atomic
    def allocate(tin: str, bhf_id: str) -> int:
        """
        Reserve the next invcNo for this branch. Never call this outside the
        same transaction that writes the EtimsInvoice outbox row — otherwise
        a rollback leaves a permanent gap that KRA will flag in audit.
        """
        if not tin or not bhf_id:
            raise ValidationError("eTIMS tin and bhfId must be configured before submission.")

        seq, created = (
            EtimsSequence.objects
            .select_for_update()
            .get_or_create(tin=tin, bhf_id=bhf_id, defaults={"next_no": 1})
        )
        allocated = seq.next_no
        seq.next_no = allocated + 1
        seq.save(update_fields=["next_no"])
        return allocated

    @staticmethod
    def peek(tin: str, bhf_id: str) -> int:
        seq = EtimsSequence.objects.filter(tin=tin, bhf_id=bhf_id).first()
        return seq.next_no if seq else 1