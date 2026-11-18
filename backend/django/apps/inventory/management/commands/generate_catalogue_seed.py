import csv
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.inventory.models import Category, Product


CATEGORY_APPLIES_TO = {
    "Motorbike Service": "MOTORBIKE",
    "Motorbike Engine & Filters": "MOTORBIKE",
    "Motorbike Brakes": "MOTORBIKE",
    "Motorbike Suspension & Steering": "MOTORBIKE",
    "Motorbike Drive & Transmission": "MOTORBIKE",
    "Motorbike Electrical": "MOTORBIKE",
    "Motorbike Cooling & Fuel": "MOTORBIKE",
    "Motorbike Body & Accessories": "MOTORBIKE",
    "Motorbike Tyres & Wheels": "MOTORBIKE",
    "Motorbike Fluids & Consumables": "MOTORBIKE",
    "Service Accessories": "BOTH",
    "Workshop Consumables": "BOTH",
}
MOTORBIKE_CATEGORIES = {
    "Motorbike Service",
    "Motorbike Engine & Filters",
    "Motorbike Brakes",
    "Motorbike Suspension & Steering",
    "Motorbike Drive & Transmission",
    "Motorbike Electrical",
    "Motorbike Cooling & Fuel",
    "Motorbike Body & Accessories",
    "Motorbike Tyres & Wheels",
    "Motorbike Fluids & Consumables",
}
ACCESSORY_CATEGORIES = {"Service Accessories", "Workshop Consumables"}
KNOWN_CATEGORIES = {
    "Engine & Service",
    "Brakes",
    "Suspension & Steering",
    "Electrical",
    "Body & Exterior",
    "Air Conditioning",
    "Transmission & Drivetrain",
    "Commercial Vehicles",
    "Motorbike Service",
    "Motorbike Engine & Filters",
    "Motorbike Brakes",
    "Motorbike Suspension & Steering",
    "Motorbike Drive & Transmission",
    "Motorbike Electrical",
    "Motorbike Cooling & Fuel",
    "Motorbike Body & Accessories",
    "Motorbike Tyres & Wheels",
    "Motorbike Fluids & Consumables",
    "Service Accessories",
    "Toyota Common",
    "Pickup & 4WD",
    "Workshop Consumables",
    "Cooling System",
}
CSV_FIELDS = (
    "sku",
    "category",
    "name",
    "product_type",
    "compatibility_notes",
    "oem_part_number",
    "price_kes",
    "is_active",
    "source_page",
)


def clean_cell(value):
    return re.sub(r"\s+", " ", value or "").strip()


def header_indexes(row):
    normalized = [clean_cell(cell).lower() for cell in row]
    if "category" not in normalized or "name" not in normalized:
        return None
    indexes = {name: normalized.index(name) for name in ("category", "name")}
    for key, aliases in {
        "compatibility": ("vehicle compatibility", "compatibility"),
        "oem": ("oem / part no.", "oem / part no", "oem / part number"),
        "price": ("price (kes)", "price"),
    }.items():
        indexes[key] = next((normalized.index(alias) for alias in aliases if alias in normalized), None)
    return indexes


def cell_at(row, index):
    if index is None or index >= len(row):
        return ""
    return clean_cell(row[index])


def extract_catalogue(pdf_path):
    try:
        import pdfplumber
    except ImportError as exc:
        raise CommandError(
            "PDF parsing requires the development requirements: "
            "pip install -r requirements/development.txt"
        ) from exc

    entries = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                indexes = None
                current_category = ""
                for row in table:
                    if not row:
                        continue
                    possible_header = header_indexes(row)
                    if possible_header:
                        indexes = possible_header
                        continue
                    if indexes is None:
                        continue

                    category = cell_at(row, indexes["category"]) or current_category
                    name = cell_at(row, indexes["name"])
                    if category in KNOWN_CATEGORIES:
                        current_category = category
                    else:
                        continue
                    if not name or name.lower() == "name":
                        continue

                    item_number = len(entries) + 1
                    product_type = (
                        "MOTORBIKE_PART" if category in MOTORBIKE_CATEGORIES
                        else "ACCESSORY" if category in ACCESSORY_CATEGORIES
                        else "AUTO_PART"
                    )
                    entries.append({
                        "sku": f"CATPDF-{item_number:04d}",
                        "category": category,
                        "name": name[:200],
                        "product_type": product_type,
                        "compatibility_notes": cell_at(row, indexes["compatibility"]),
                        "oem_part_number": cell_at(row, indexes["oem"]),
                        "price_kes": cell_at(row, indexes["price"]),
                        "is_active": "false",
                        "source_page": page_number,
                    })
    return entries


def load_builtin_catalogue():
    project_root = Path(settings.BASE_DIR).parent.parent
    catalogue_path = Path(__file__).with_name("reference_catalogue.tsv")

    if catalogue_path.is_file():
        entries = []
        with catalogue_path.open(encoding="utf-8", newline="") as catalogue_file:
            reader = csv.DictReader(catalogue_file, delimiter="\t")
            for index, row in enumerate(reader, start=1):
                category = clean_cell(row.get("category"))
                name = clean_cell(row.get("name"))
                product_type = clean_cell(row.get("product_type")) or "AUTO_PART"
                if not category or not name:
                    continue
                if category not in KNOWN_CATEGORIES:
                    raise CommandError(f"Unknown built-in catalogue category: {category}")
                if product_type not in {"AUTO_PART", "MOTORBIKE_PART", "ACCESSORY"}:
                    raise CommandError(f"Invalid product type for {name}: {product_type}")

                entries.append({
                    "source_sku": f"CATPDF-{index:04d}",
                    "category": category,
                    "name": name,
                    "product_type": product_type,
                    "compatibility_notes": clean_cell(row.get("compatibility_notes")),
                    "oem_part_number": clean_cell(row.get("oem_part_number")),
                })

        if len(entries) != 402:
            raise CommandError(
                f"Expected 402 rows in {catalogue_path}, found {len(entries)}. "
                "The built-in catalogue was not exported or seeded."
            )
        return entries

    pdf_path = project_root / "auto_motorbike_spare_parts_catalogue.pdf"
    if pdf_path.is_file():
        entries = extract_catalogue(pdf_path)
        if len(entries) != 402:
            raise CommandError(
                f"Expected 402 catalogue rows from the PDF, extracted {len(entries)}. "
                "The built-in catalogue was not exported or seeded."
            )
        for entry in entries:
            entry["source_sku"] = entry["sku"]
            entry["oem_part_number"] = entry.get("oem_part_number", "")
        return entries

    raise CommandError(
        "Built-in catalogue source not found. Add auto_motorbike_spare_parts_seed.csv "
        "or auto_motorbike_spare_parts_catalogue.pdf at the project root/data location."
    )


class Command(BaseCommand):
    help = "Seed the DEMKA spare-parts catalogue from built-in CSV or --file."

    def add_arguments(self, parser):
        project_root = Path(settings.BASE_DIR).parent.parent
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument(
            "--built-in", action="store_true",
            help="Use the built-in 402-row catalogue CSV.",
        )
        source.add_argument(
            "--file", metavar="PATH",
            help="Read a raw catalogue CSV.",
        )
        parser.add_argument("--seed", action="store_true", help="Write to the database.")
        parser.add_argument("--dump", metavar="PATH", help="Write combined CSV and do not seed.")
        parser.add_argument("--reset", action="store_true", help="Delete existing products in target categories.")
        parser.add_argument("--activate", action="store_true", help="Mark seeded products active.")
        parser.add_argument("--limit", type=int, metavar="N", help="Seed only the first N products.")
        parser.add_argument("--default-cost", type=float, default=0.0)
        parser.add_argument("--default-retail", type=float, default=0.0)
        parser.add_argument("--default-wholesale", type=float, default=0.0)

    def handle(self, *args, **options):
        if options["built_in"]:
            products = load_builtin_catalogue()
            source_label = "built-in 402-row CSV"
        else:
            products = self._from_csv(options["file"])
            source_label = options["file"]

        if options["limit"]:
            products = products[:options["limit"]]

        if not products:
            raise CommandError("No catalogue products were found.")

        if options["dump"]:
            self._dump_csv(products, options["dump"])
            self.stdout.write(self.style.SUCCESS(f"Wrote {len(products)} combined entries to {options['dump']}"))
            return

        if not options["seed"]:
            self.stdout.write(self.style.WARNING("[DRY RUN] Pass --seed to write to the database."))

        self.stdout.write(self.style.HTTP_INFO(
            f"Source: {source_label} ({len(products)} products)"
        ))

        stats = self._seed(products, options)
        self._print_summary(stats, len(products), options)

    def _from_csv(self, path):
        csv_path = Path(path)
        if not csv_path.is_file():
            raise CommandError(f"CSV file not found: {csv_path}")

        products = []
        with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            required = {"sku", "category", "name", "product_type", "compatibility_notes"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise CommandError(f"CSV missing required column(s): {', '.join(sorted(missing))}")

            for row in reader:
                category = clean_cell(row.get("category"))
                name = clean_cell(row.get("name"))
                product_type = clean_cell(row.get("product_type")) or "AUTO_PART"
                source_sku = clean_cell(row.get("sku"))
                oem_part_number = clean_cell(row.get("oem_part_number"))

                if not category or not name:
                    continue
                if category not in KNOWN_CATEGORIES:
                    raise CommandError(f"Unknown catalogue category: {category}")
                if product_type not in {"AUTO_PART", "MOTORBIKE_PART", "ACCESSORY"}:
                    raise CommandError(f"Invalid product type for {name}: {product_type}")

                variants = [
                    variant.strip()
                    for variant in clean_cell(row.get("compatibility_notes")).split(",")
                    if variant.strip()
                ] or [""]

                for variant in variants:
                    products.append({
                        "source_sku": source_sku,
                        "category": category,
                        "name": f"{name} – {variant}" if variant else name,
                        "product_type": product_type,
                        "compatibility_notes": variant,
                        "oem_part_number": oem_part_number,
                    })
        return products

    @staticmethod
    def _variant_sku(source_sku, variant):
        if not source_sku:
            return ""
        import hashlib
        suffix = hashlib.md5((variant or "").encode("utf-8")).hexdigest()[:6].upper()
        return f"{source_sku}-{suffix}"

    def _seed(self, products, options):
        stats = {"created": 0, "updated": 0, "categories": set(), "dry_run": not options["seed"]}

        if options["reset"] and options["seed"]:
            target_categories = {product["category"] for product in products}
            deleted, _ = Product.objects.filter(category__name__in=target_categories).delete()
            self.stdout.write(self.style.WARNING(f"Reset deleted {deleted} existing products"))

        for product in products:
            sku = self._variant_sku(product["source_sku"], product["compatibility_notes"])
            if not sku:
                sku = f"CAT-{len(stats['categories']) + 1:04d}"

            if not options["seed"]:
                self.stdout.write(f"  [DRY] {product['category']:<34} {sku:<24} {product['name']}")
                continue

            category, _ = Category.objects.get_or_create(
                name=product["category"],
                defaults={"applies_to": CATEGORY_APPLIES_TO.get(product["category"], "AUTO")},
            )
            stats["categories"].add(category.pk)

            _, created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": product["name"][:200],
                    "part_number": product["oem_part_number"][:100],
                    "category": category,
                    "product_type": product["product_type"],
                    "compatibility_notes": product["compatibility_notes"],
                    "cost_price": options["default_cost"],
                    "retail_price": options["default_retail"],
                    "wholesale_price": options["default_wholesale"],
                    "is_stocked": False,
                    "is_active": options["activate"],
                    "reorder_level": 5,
                    "reorder_qty": 10,
                },
            )
            stats["created" if created else "updated"] += 1

        return stats

    def _dump_csv(self, products, path):
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["category", "product_type", "name", "compatibility_notes", "oem_part_number"])
            for product in products:
                writer.writerow([
                    product["category"], product["product_type"], product["name"],
                    product["compatibility_notes"], product["oem_part_number"],
                ])

    def _print_summary(self, stats, product_count, options):
        if stats["dry_run"]:
            self.stdout.write(self.style.SUCCESS(
                f"[DRY RUN] {product_count} products ready. No database changes made."
            ))
            return
        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {stats['created']} created, {stats['updated']} updated."
        ))
        state = "ACTIVE" if options["activate"] else "INACTIVE"
        self.stdout.write(f"Products are {state} and unstocked.")
