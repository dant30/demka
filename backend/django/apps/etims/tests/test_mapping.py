from decimal import Decimal

from django.test import TestCase

from apps.common.models import TaxRate
from apps.etims.services.mapping import EtimsMappingError, PaymentMapper, TaxMapper


class TaxMapperTests(TestCase):
    def test_code_from_taxrate(self):
        tr = TaxRate.objects.create(
            name="Std", rate=Decimal("16.00"), etims_code="B",
            effective_from="2026-01-01",
        )
        item = type("I", (), {"tax_rate_ref": tr, "tax_rate": Decimal("16.00"), "pk": 1})()
        self.assertEqual(TaxMapper.code_for_sale_item(item), "B")

    def test_code_from_rate_fallback(self):
        item = type("I", (), {
            "tax_rate_ref": None, "tax_rate": Decimal("16.00"), "pk": 1,
        })()
        self.assertEqual(TaxMapper.code_for_sale_item(item), "B")

    def test_unknown_rate_raises(self):
        item = type("I", (), {
            "tax_rate_ref": None, "tax_rate": Decimal("12.00"), "pk": 1,
        })()
        with self.assertRaises(EtimsMappingError):
            TaxMapper.code_for_sale_item(item)


class PaymentMapperTests(TestCase):
    def test_cash(self):
        self.assertEqual(PaymentMapper.code_for_method("CASH"), "01")

    def test_mpesa(self):
        self.assertEqual(PaymentMapper.code_for_method("MPESA"), "04")

    def test_unknown_defaults_to_other(self):
        self.assertEqual(PaymentMapper.code_for_method("WEIRD"), "06")