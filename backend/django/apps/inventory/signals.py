"""Inventory signals — cache invalidation on stock level changes."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.cache.invalidation import invalidate_stock

from .models import StockLevel


@receiver(post_save, sender=StockLevel)
def stock_level_post_save(sender, instance, **kwargs):
    invalidate_stock(instance.product_id)