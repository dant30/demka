"""KRA-ready VAT summary, net of completed returns."""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from core.utils.money import q


MONEY = DecimalField(max_digits=14, decimal_places=2)
QUALIFYING_STATUSES = ["CONFIRMED", "PAID", "PARTIAL", "INVOICED"]


class TaxReportingService:
    @staticmethod
    def _bucket_from_gross(gross: Decimal, rate: Decimal) -> tuple[Decimal, Decimal]:
        if rate <= 0:
            return q(gross), Decimal("0.00")
        taxable = q(gross / (Decimal("1") + rate / Decimal("100")))
        return taxable, q(gross - taxable)

    @staticmethod
    def _aggregate_sales(start: date, end: date) -> dict:
        from apps.sales.models import SaleItem

        rows = (
            SaleItem.objects.filter(
                sale__status__in=QUALIFYING_STATUSES,
                sale__confirmed_at__date__gte=start,
                sale__confirmed_at__date__lte=end,
            )
            .values("tax_rate", "tax_rate_ref__etims_code", "tax_rate_ref__name")
            .annotate(gross=Sum("line_total"))
        )
        buckets = defaultdict(lambda: {"taxable": Decimal("0"), "tax": Decimal("0"), "gross": Decimal("0")})
        for row in rows:
            rate = Decimal(str(row["tax_rate"] or 0))
            code = row["tax_rate_ref__etims_code"] or f"R{rate}"
            gross = Decimal(str(row["gross"] or 0))
            taxable, tax = TaxReportingService._bucket_from_gross(gross, rate)
            bucket = buckets[code]
            bucket["taxable"] += taxable
            bucket["tax"] += tax
            bucket["gross"] += gross
            bucket["name"] = row["tax_rate_ref__name"] or f"{rate}%"
            bucket["rate"] = str(rate)
        return buckets

    @staticmethod
    def _aggregate_returns(start: date, end: date) -> dict:
        from apps.sales.models import SalesReturnItem

        rows = (
            SalesReturnItem.objects.filter(
                sales_return__status="COMPLETED",
                sales_return__created_at__date__gte=start,
                sales_return__created_at__date__lte=end,
            )
            .values(
                "sale_item__tax_rate", "sale_item__tax_rate_ref__etims_code",
                "sale_item__tax_rate_ref__name",
            )
            .annotate(gross=Sum(ExpressionWrapper(
                F("quantity") * F("unit_price"), output_field=MONEY,
            )))
        )
        buckets = defaultdict(lambda: {"taxable": Decimal("0"), "tax": Decimal("0"), "gross": Decimal("0")})
        for row in rows:
            rate = Decimal(str(row["sale_item__tax_rate"] or 0))
            code = row["sale_item__tax_rate_ref__etims_code"] or f"R{rate}"
            gross = Decimal(str(row["gross"] or 0))
            taxable, tax = TaxReportingService._bucket_from_gross(gross, rate)
            bucket = buckets[code]
            bucket["taxable"] += taxable
            bucket["tax"] += tax
            bucket["gross"] += gross
            bucket["name"] = row["sale_item__tax_rate_ref__name"] or f"{rate}%"
            bucket["rate"] = str(rate)
        return buckets

    @staticmethod
    def vat_summary(start: date, end: date) -> dict:
        sales = TaxReportingService._aggregate_sales(start, end)
        returns = TaxReportingService._aggregate_returns(start, end)
        rows = []
        total_taxable = Decimal("0")
        total_tax = Decimal("0")
        for code in sorted(set(sales) | set(returns)):
            sale = sales.get(code, {})
            returned = returns.get(code, {})
            net_taxable = q(sale.get("taxable", 0) - returned.get("taxable", 0))
            net_tax = q(sale.get("tax", 0) - returned.get("tax", 0))
            rows.append({
                "code": code,
                "name": sale.get("name") or returned.get("name") or code,
                "rate": sale.get("rate") or returned.get("rate") or "0",
                "gross_sales": str(q(sale.get("gross", 0))),
                "taxable_base": str(net_taxable),
                "vat_collected": str(net_tax),
                "gross_returns": str(q(returned.get("gross", 0))),
            })
            total_taxable += net_taxable
            total_tax += net_tax
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "by_tax_code": rows,
            "total_taxable_base": str(q(total_taxable)),
            "total_vat": str(q(total_tax)),
        }
