"""Sales signals — cache invalidation on sale status changes."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Sale


@receiver(post_save, sender=Sale)
def sale_post_save(sender, instance, **kwargs):
    # invalidate stock caches for the products in this sale — cheap safety net
    from core.cache.invalidation import invalidate_stock
    for item in instance.items.all() if instance.pk else []:
        invalidate_stock(item.product_id)