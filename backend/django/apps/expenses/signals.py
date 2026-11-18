"""Expenses signals — cache invalidation for monthly digests."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Expense


@receiver([post_save, post_delete], sender=Expense)
def expense_changed(sender, instance, **kwargs):
    """Expense totals are cached by month/category; drop the month cache."""
    from django.core.cache import cache
    if hasattr(cache, "delete_pattern"):
        key = f"expenses:month:{instance.expense_date:%Y-%m}"
        cache.delete(key)