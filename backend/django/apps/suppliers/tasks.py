from celery import shared_task


@shared_task
def prune_orphan_supplier_products() -> dict:
    """
    Remove SupplierProduct rows whose product has become inactive *and*
    has no purchase history. Safe because SupplierProduct rows carry
    no financial state — historical POs keep their own copies.
    """
    from apps.inventory.models import Product
    from .models import SupplierProduct

    inactive_ids = Product.objects.filter(is_active=False).values_list("id", flat=True)
    qs = SupplierProduct.objects.filter(product_id__in=inactive_ids)
    removed, _ = qs.delete()
    return {"removed": removed}