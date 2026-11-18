from django.db import models


class GoodsReceivedNote(models.Model):
    grn_number = models.CharField(max_length=30, unique=True)
    po = models.ForeignKey("purchasing.PurchaseOrder", null=True, blank=True, on_delete=models.SET_NULL)
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT)
    received_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    received_at = models.DateTimeField(auto_now_add=True)
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)


class GoodsReceivedItem(models.Model):
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name="items")
    po_item = models.ForeignKey("purchasing.PurchaseOrderItem", null=True, blank=True, on_delete=models.SET_NULL)
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)