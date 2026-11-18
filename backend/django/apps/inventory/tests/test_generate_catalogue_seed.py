import csv
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase


class BuiltInCatalogueCommandTests(SimpleTestCase):
    def test_builtin_tsv_contains_catalogue(self):
        catalogue_path = (
            Path(__file__).parent.parent
            / "management"
            / "commands"
            / "reference_catalogue.tsv"
        )
        with catalogue_path.open(encoding="utf-8", newline="") as catalogue_file:
            entries = list(csv.DictReader(catalogue_file, delimiter="\t"))

        self.assertEqual(len(entries), 402)
        self.assertTrue(all(entry["category"] for entry in entries))
        self.assertTrue(all(entry["name"] for entry in entries))
        self.assertTrue(all(entry["product_type"] in {
            "AUTO_PART", "MOTORBIKE_PART", "ACCESSORY"
        } for entry in entries))

    def test_raw_csv_splits_compatibility_variants(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "catalogue.csv"
            csv_path.write_text(
                "sku,category,name,product_type,compatibility_notes,oem_part_number,price_kes,is_active,source_page\n"
                "TEST-0001,Engine & Service,Oil Filter,AUTO_PART,\"Toyota Corolla, Toyota Hilux\",,0,false,1\n",
                encoding="utf-8",
            )
            with tempfile.TemporaryDirectory() as output_dir:
                output_path = Path(output_dir) / "combined.csv"
                call_command(
                    "generate_catalogue_seed",
                    file=str(csv_path),
                    dump=str(output_path),
                )

                with output_path.open(encoding="utf-8", newline="") as output_file:
                    rows = list(csv.DictReader(output_file))

        self.assertEqual(len(rows), 2)
        self.assertIn("Toyota Corolla", rows[0]["name"])
        self.assertIn("Toyota Hilux", rows[1]["name"])
