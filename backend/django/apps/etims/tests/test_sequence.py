from django.test import TestCase

from apps.etims.models import EtimsSequence
from apps.etims.services.sequence import SequenceService


class SequenceTests(TestCase):
    def test_allocates_monotonic(self):
        a = SequenceService.allocate("P1", "00")
        b = SequenceService.allocate("P1", "00")
        c = SequenceService.allocate("P1", "00")
        self.assertEqual((a, b, c), (1, 2, 3))

    def test_per_branch_isolated(self):
        SequenceService.allocate("P1", "00")
        SequenceService.allocate("P1", "00")
        first_b01 = SequenceService.allocate("P1", "01")
        self.assertEqual(first_b01, 1)

    def test_peek_does_not_advance(self):
        SequenceService.allocate("P1", "00")
        self.assertEqual(SequenceService.peek("P1", "00"), 2)
        self.assertEqual(SequenceService.peek("P1", "00"), 2)