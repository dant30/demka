from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.etims.models import EtimsConfig, EtimsItem
from apps.etims.services.client import EtimsClient, EtimsError, EtimsRejection
from apps.inventory.models import Product


class Command(BaseCommand):
    help = "Register every active product with a valid etims_item_cls_cd against KRA."

    def add_arguments(self, parser):
        parser.add_argument("--sku", help="Register only this SKU.")
        parser.add_argument("--force", action="store_true", help="Re-register already-registered items.")

    def handle(self, *args, **options):
        cfg = EtimsConfig.get_solo()
        if not cfg.cmc_key:
            raise SystemExit("Device not initialised. Run etims_init_device first.")
        client = EtimsClient(cfg)

        qs = Product.objects.filter(is_active=True).exclude(etims_item_cls_cd="")
        if options.get("sku"):
            qs = qs.filter(sku=options["sku"])
        if not options.get("force"):
            registered_ids = EtimsItem.objects.filter(
                status=EtimsItem.Status.REGISTERED,
            ).values_list("product_id", flat=True)
            qs = qs.exclude(pk__in=registered_ids)

        ok, failed, skipped = 0, 0, 0
        for product in qs.iterator():
            if not product.etims_item_cls_cd:
                skipped += 1
                continue
            payload = {
                "tin": cfg.tin,
                "bhfId": cfg.bhf_id,
                "itemCd": product.sku,
                "itemClsCd": product.etims_item_cls_cd,
                "itemTyCd": product.etims_item_type or "2",
                "itemNm": product.name[:200],
                "itemStdNm": product.name[:200],
                "orgnNatCd": "KE",
                "pkgUnitCd": "NT",
                "qtyUnitCd": "U",
                "taxTyCd": getattr(product, "etims_tax_code", "B") or "B",
                "btchNo": None,
                "bcd": product.barcode or None,
                "dftPrc": float(product.retail_price or 0),
                "addInfo": product.compatibility_notes[:200] if product.compatibility_notes else "",
                "sftyQty": int(product.reorder_level or 0),
                "isrcAplcbYn": "N",
                "useYn": "Y",
                "regrId": "system",
                "regrNm": "System",
                "modrId": "system",
                "modrNm": "System",
            }
            try:
                body = client.save_item(payload)
            except EtimsRejection as exc:
                failed += 1
                EtimsItem.objects.update_or_create(
                    product=product,
                    defaults={
                        "item_cd": product.sku, "item_cls_cd": product.etims_item_cls_cd,
                        "status": EtimsItem.Status.FAILED,
                        "response_payload": exc.raw, "error_message": str(exc),
                    },
                )
                self.stderr.write(f"  ✗ {product.sku}: {exc.result_cd} {exc.result_msg}")
                continue
            except EtimsError as exc:
                failed += 1
                self.stderr.write(f"  ✗ {product.sku}: {exc}")
                continue

            ok += 1
            EtimsItem.objects.update_or_create(
                product=product,
                defaults={
                    "item_cd": product.sku, "item_cls_cd": product.etims_item_cls_cd,
                    "status": EtimsItem.Status.REGISTERED,
                    "response_payload": body,
                    "error_message": "",
                    "registered_at": timezone.now(),
                },
            )
            self.stdout.write(f"  ✓ {product.sku}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. registered={ok} failed={failed} skipped={skipped}",
        ))