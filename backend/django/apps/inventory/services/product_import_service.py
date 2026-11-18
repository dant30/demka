"""
Excel/CSV product import pipeline.

    parse(file)     → list of row dicts with raw + parsed data + errors + warnings
    preview(...)    → summary without touching the DB
    commit(...)     → atomic (all-or-nothing) OR partial (skip invalid rows)

Design principles:
    * Excel cells are normalized defensively (floats, None, booleans, strings).
    * Categories are matched case-insensitively and auto-created.
    * SKU + barcode uniqueness checked against DB AND against the file itself.
    * Rows with warnings (e.g. retail < cost) still import — errors block them.
    * All writes happen in one transaction; a mid-file failure rolls back cleanly.
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Iterable, Iterator

from django.db import transaction

from core.exceptions.domain import ValidationError

from ..models import Category, Product


ALLOWED_PRODUCT_TYPES = {"MOTORBIKE_PART", "AUTO_PART", "ACCESSORY"}
ALLOWED_UNITS = {"PIECE", "SET", "PAIR", "LITRE"}
REQUIRED_FIELDS = {"sku", "name", "category", "retail_price", "wholesale_price"}
MAX_ROW_ERRORS = 10_000  # safety cap — do not let a bad file OOM the server


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _read_rows(file) -> Iterator[dict]:
    """Yield dicts keyed by lowercased header names, from .xlsx or .csv."""
    name = (getattr(file, "name", "") or "").lower()
    file.seek(0)

    if name.endswith(".csv"):
        raw = file.read()
        if isinstance(raw, bytes):
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
        else:
            text = raw
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValidationError("CSV file has no headers.")
        mapping = {(h or "").strip().lower(): h for h in reader.fieldnames}
        for row in reader:
            yield {k: row.get(orig) for k, orig in mapping.items()}
        return

    # Excel
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise ValidationError("openpyxl is not installed on the server.")

    file.seek(0)
    try:
        wb = load_workbook(file, read_only=True, data_only=True)
    except Exception as exc:
        raise ValidationError(f"Cannot read Excel file: {exc}")

    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header_row = next(rows, None)
    if not header_row:
        raise ValidationError("Excel file is empty.")

    headers = [
        (str(h).strip().lower() if h is not None else "")
        for h in header_row
    ]
    for row in rows:
        yield dict(zip(headers, row))
    wb.close()


def _clean_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _as_decimal(value, field: str, errors: list) -> Decimal:
    if value is None or value == "":
        return Decimal("0.00")
    try:
        d = Decimal(str(value))
        if d < 0:
            errors.append(f"{field} cannot be negative")
            return Decimal("0.00")
        return d.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        errors.append(f"Invalid {field}: {value!r}")
        return Decimal("0.00")


def _as_int(value, field: str, errors: list, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        i = int(float(value))
        if i < 0:
            errors.append(f"{field} cannot be negative")
            return default
        return i
    except (ValueError, TypeError):
        errors.append(f"Invalid {field}: {value!r}")
        return default


def _as_bool(value, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return _clean_str(value).lower() in ("true", "1", "yes", "y", "t")


def _parse_row(row: dict, row_number: int, taken_skus: set, taken_barcodes: set) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    sku = _clean_str(row.get("sku"))
    part_number = _clean_str(row.get("part_number"))
    name = _clean_str(row.get("name"))
    category_name = _clean_str(row.get("category"))

    if not sku:
        errors.append("Missing required field: sku")
    elif sku in taken_skus:
        errors.append(f"Duplicate sku: {sku}")
    else:
        taken_skus.add(sku)

    if not name:
        errors.append("Missing required field: name")
    elif len(name) > 200:
        errors.append(f"name exceeds 200 characters ({len(name)}).")

    if len(part_number) > 100:
        errors.append(f"part_number exceeds 100 characters ({len(part_number)}).")

    if not category_name:
        errors.append("Missing required field: category")

    product_type = _clean_str(row.get("product_type")).upper() or "AUTO_PART"
    if product_type not in ALLOWED_PRODUCT_TYPES:
        errors.append(
            f"Invalid product_type: {product_type!r} "
            f"(must be one of {sorted(ALLOWED_PRODUCT_TYPES)})"
        )
        product_type = "AUTO_PART"

    unit = _clean_str(row.get("unit")).upper() or "PIECE"
    if unit not in ALLOWED_UNITS:
        errors.append(
            f"Invalid unit: {unit!r} (must be one of {sorted(ALLOWED_UNITS)})"
        )
        unit = "PIECE"

    cost = _as_decimal(row.get("cost_price"), "cost_price", errors)
    retail = _as_decimal(row.get("retail_price"), "retail_price", errors)
    wholesale = _as_decimal(row.get("wholesale_price"), "wholesale_price", errors)

    if retail <= 0:
        errors.append("retail_price must be greater than 0")
    if wholesale <= 0:
        errors.append("wholesale_price must be greater than 0")
    if cost > 0 and retail > 0 and retail < cost:
        warnings.append("retail_price is below cost_price")
    if cost > 0 and wholesale > 0 and wholesale < cost:
        warnings.append("wholesale_price is below cost_price")

    barcode = _clean_str(row.get("barcode"))
    if barcode:
        if len(barcode) > 50:
            errors.append("barcode exceeds 50 characters")
            barcode = barcode[:50]
        elif barcode in taken_barcodes:
            errors.append(f"Duplicate barcode: {barcode}")
            barcode = ""
        else:
            taken_barcodes.add(barcode)

    reorder_level = _as_int(row.get("reorder_level"), "reorder_level", errors)
    reorder_qty = _as_int(row.get("reorder_qty"), "reorder_qty", errors)

    return {
        "row": row_number,
        "sku": sku,
        "name": name,
        "errors": errors,
        "warnings": warnings,
        "data": {
            "sku": sku,
            "part_number": part_number,
            "name": name,
            "category_name": category_name,
            "product_type": product_type,
            "brand": _clean_str(row.get("brand"))[:100],
            "unit": unit,
            "cost_price": cost,
            "retail_price": retail,
            "wholesale_price": wholesale,
            "is_stocked": _as_bool(row.get("is_stocked"), default=False),
            "reorder_level": reorder_level,
            "reorder_qty": reorder_qty,
            "barcode": barcode or None,
            "compatibility_notes": _clean_str(row.get("compatibility_notes")),
            "etims_item_cls_cd": _clean_str(row.get("etims_item_cls_cd"))[:20],
        },
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class ProductImportService:

    @staticmethod
    def import_file(file, *, user, mode: str = "preview", skip_errors: bool = False) -> dict:
        if mode not in ("preview", "commit"):
            raise ValidationError("mode must be 'preview' or 'commit'.")

        # Build taken sets from DB.
        existing_skus = set(Product.objects.values_list("sku", flat=True))
        existing_barcodes = set(
            Product.objects
            .exclude(barcode__isnull=True)
            .exclude(barcode="")
            .values_list("barcode", flat=True)
        )

        parsed: list[dict] = []
        taken_skus: set[str] = set(existing_skus)
        taken_barcodes: set[str] = set(existing_barcodes)
        file_skus: set[str] = set()

        # Row 1 is the header → data starts at row 2.
        for idx, raw_row in enumerate(_read_rows(file), start=2):
            # Skip fully blank rows.
            if not any(v not in (None, "") for v in raw_row.values()):
                continue

            # Skip rows whose SKU hasn't been seen in this file, but only
            # mark seen after parsing succeeds — that way the same bad row
            # repeated twice doesn't double-count.
            parsed_row = _parse_row(raw_row, idx, taken_skus, taken_barcodes)
            file_skus.add(parsed_row["sku"])
            parsed.append(parsed_row)

            if len(parsed) > MAX_ROW_ERRORS:
                raise ValidationError(
                    f"File exceeds the {MAX_ROW_ERRORS} row limit."
                )

        valid = [r for r in parsed if not r["errors"]]
        invalid = [r for r in parsed if r["errors"]]

        summary = {
            "mode": mode,
            "total": len(parsed),
            "valid": len(valid),
            "invalid": len(invalid),
            "warnings": sum(1 for r in parsed if r["warnings"]),
            "created": 0,
            "errors": [
                {
                    "row": r["row"],
                    "sku": r["sku"] or "(blank)",
                    "name": r["name"],
                    "messages": r["errors"],
                }
                for r in invalid
            ],
            "preview": [
                {
                    "row": r["row"],
                    "sku": r["sku"],
                    "part_number": r["data"]["part_number"],
                    "name": r["name"],
                    "category": r["data"]["category_name"],
                    "product_type": r["data"]["product_type"],
                    "retail_price": str(r["data"]["retail_price"]),
                    "wholesale_price": str(r["data"]["wholesale_price"]),
                    "status": "error" if r["errors"] else ("warning" if r["warnings"] else "ok"),
                }
                for r in parsed[:100]  # cap preview
            ],
            "truncated_preview": len(parsed) > 100,
        }

        if mode == "preview":
            return summary

        # ---- Commit -------------------------------------------
        if invalid and not skip_errors:
            summary["aborted"] = True
            summary["reason"] = (
                f"{len(invalid)} row(s) have errors. "
                f"Tick 'Skip invalid rows' to import the {len(valid)} valid rows, "
                f"or fix the file and re-upload."
            )
            return summary

        if not valid:
            summary["aborted"] = True
            summary["reason"] = "No valid rows to import."
            return summary

        created = ProductImportService._create_products(valid, user)
        summary["created"] = created
        return summary

    # -----------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def _create_products(rows: list[dict], user) -> int:
        # 1. Resolve categories (case-insensitive match, auto-create missing)
        category_lookup: dict[str, Category] = {}
        unique_names = {r["data"]["category_name"].strip() for r in rows}

        for name in unique_names:
            key = name.lower()
            cat = Category.objects.filter(name__iexact=name).first()
            if not cat:
                cat = Category.objects.create(name=name)
            category_lookup[key] = cat

        # 2. Build Product instances
        products: list[Product] = []
        for r in rows:
            d = r["data"]
            cat = category_lookup[d["category_name"].strip().lower()]
            products.append(
                Product(
                    sku=d["sku"],
                    part_number=d["part_number"],
                    name=d["name"],
                    description="",
                    category=cat,
                    product_type=d["product_type"],
                    brand=d["brand"],
                    unit=d["unit"],
                    cost_price=d["cost_price"],
                    retail_price=d["retail_price"],
                    wholesale_price=d["wholesale_price"],
                    is_stocked=d["is_stocked"],
                    reorder_level=d["reorder_level"],
                    reorder_qty=d["reorder_qty"],
                    barcode=d["barcode"],
                    compatibility_notes=d["compatibility_notes"],
                    etims_item_cls_cd=d["etims_item_cls_cd"],
                    is_active=True,
                )
            )

        # 3. Insert
        Product.objects.bulk_create(products, batch_size=200)

        # 4. Audit trail — one entry summarising the bulk import
        try:
            from apps.accounts.models import AuditLog
            AuditLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                action="BULK_IMPORT",
                model_name="Product",
                object_id="",
                changes={"created": len(products)},
            )
        except Exception:
            pass  # never fail the import on an audit hiccup

        return len(products)