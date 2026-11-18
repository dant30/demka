"""
ESC/POS byte-stream renderer — no external dependencies.

Receipt structure (58 mm = 32 chars, 80 mm = 48 chars at Font A):

    ┌─────────────────────────────────────┐
    │            DEMKA                    │  ← centered, bold, double-height
    │         Auto Spares & Parts          │
    │  KRA PIN: P051234567A  Tel: 0712…   │
    │ ─────────────────────────────────── │  ← divider
    │ Receipt: SL-000042   Date: 2026-…   │
    │ Cashier: J. Doe     Till: Main      │
    │ Customer: Acme Traders              │
    │ ─────────────────────────────────── │
    │ Item              Qty   Price   Tot │  ← header, bold
    │ Piston Ring      2×    130.00  260  │
    │ Brake Pad        1×    450.00  450  │
    │ ─────────────────────────────────── │
    │                  Subtotal   710.00  │
    │                  VAT (16%)  113.60  │
    │                  Total      823.60  │
    │                  Paid       823.60  │
    │                  Balance      0.00  │
    │ ─────────────────────────────────── │
    │         Asante! Karibu tena         │  ← centered
    │                                     │
    │           [QR: KRA eTIMS]           │  ← if eTIMS stamped
    │                                     │
    │                                     │  ← feed before cut
    └─────────────────────────────────────┘

Every byte-writing method returns self so blocks can be chained:

    r = ReceiptRenderer(width=32)
    r.line("DEMKA", bold=True, double_height=True, align="center")
    r.rule()
    r.cut()
    data = r.bytes()
"""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable


# ---------------------------------------------------------------------------
# ESC/POS command constants
# ---------------------------------------------------------------------------
ESC = b"\x1b"
GS = b"\x1d"
FS = b"\x1c"

CMD_INIT          = ESC + b"@"                     # ESC @
CMD_ALIGN_LEFT    = ESC + b"a\x00"                 # ESC a 0
CMD_ALIGN_CENTER  = ESC + b"a\x01"                 # ESC a 1
CMD_ALIGN_RIGHT   = ESC + b"a\x02"                 # ESC a 2
CMD_BOLD_ON       = ESC + b"E\x01"                 # ESC E 1
CMD_BOLD_OFF      = ESC + b"E\x00"                 # ESC E 0
CMD_UNDERLINE_ON  = ESC + b"-\x01"                 # ESC - 1
CMD_UNDERLINE_OFF = ESC + b"-\x00"                 # ESC - 0
CMD_DOUBLE_ON     = GS + b"!\x11"                  # GS ! 0x11 = double w & h
CMD_DOUBLE_OFF    = GS + b"!\x00"                  # GS ! 0x00 = normal
CMD_FONT_A        = ESC + b"M\x00"                 # ESC M 0
CMD_FONT_B        = ESC + b"M\x01"                 # ESC M 1
CMD_CUT_PARTIAL   = GS + b"V\x01"                  # GS V 1 = partial cut
CMD_CUT_FULL      = GS + b"V\x00"                  # GS V 0 = full cut
CMD_FEED_AND_CUT  = GS + b"V\x41\x03"              # feed 3 lines, then cut
CMD_OPEN_DRAWER   = ESC + b"p\x00\x19\xfa"         # ESC p m t1 t2
CMD_LINE_FEED     = b"\n"


def _feed(n: int = 1) -> bytes:
    return ESC + b"d" + bytes([n])


def _text_bold(*, enabled: bool) -> bytes:
    return CMD_BOLD_ON if enabled else CMD_BOLD_OFF


def _text_double(*, enabled: bool) -> bytes:
    return CMD_DOUBLE_ON if enabled else CMD_DOUBLE_OFF


def _align_code(align: str) -> bytes:
    return {
        "left":   CMD_ALIGN_LEFT,
        "center": CMD_ALIGN_CENTER,
        "right":  CMD_ALIGN_RIGHT,
    }.get(align, CMD_ALIGN_LEFT)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------
class ReceiptRenderer:
    """
    Line-oriented ESC/POS builder.

    Callers describe the receipt in structured terms (line/rule/two_col/qr/cut);
    the renderer translates to bytes. All widths are in characters at Font A:
        58 mm → 32 chars
        80 mm → 48 chars
    """

    def __init__(self, width: int = 32, *, codepage: str = "cp437"):
        self.width = width
        self.codepage = codepage
        self._buffer: list[bytes] = []

    # ---- Core primitives -------------------------------------
    def reset(self):
        self._buffer.append(CMD_INIT)
        return self

    def newline(self, n: int = 1):
        self._buffer.append(CMD_LINE_FEED * n)
        return self

    def feed(self, n: int = 1):
        self._buffer.append(_feed(n))
        return self

    def raw(self, data: bytes):
        self._buffer.append(data)
        return self

    # ---- Text ------------------------------------------------
    def line(
        self,
        text: str = "",
        *,
        align: str = "left",
        bold: bool = False,
        double_height: bool = False,
        underline: bool = False,
        font_b: bool = False,
    ):
        chunks = [_align_code(align)]
        if font_b:
            chunks.append(CMD_FONT_B)
        if bold:
            chunks.append(_text_bold(enabled=True))
        if double_height:
            chunks.append(_text_double(enabled=True))
        if underline:
            chunks.append(CMD_UNDERLINE_ON)

        # KRA receipts are ASCII / Latin-1; fall back if a glyph can't encode.
        safe = text.encode(self.codepage, errors="replace")
        chunks.append(safe + CMD_LINE_FEED)

        if underline:
            chunks.append(CMD_UNDERLINE_OFF)
        if double_height:
            chunks.append(_text_double(enabled=False))
        if bold:
            chunks.append(_text_bold(enabled=False))
        if font_b:
            chunks.append(CMD_FONT_A)

        self._buffer.extend(chunks)
        return self

    def rule(self, char: str = "-"):
        self._buffer.append(
            (char * self.width).encode(self.codepage, errors="replace") + CMD_LINE_FEED
        )
        return self

    # ---- Two-column rows -------------------------------------
    def two_col(
        self,
        left: str,
        right: str,
        *,
        bold: bool = False,
        sep: str = "",
    ):
        """
        Right-align `right` and left-align `left` on the same line.
        Truncates `left` if too long. Handles degenerate widths gracefully.
        """
        if sep:
            right_str = f"{sep}{right}"
        else:
            right_str = right

        avail = self.width - len(right_str)
        if avail <= 0:
            # Fall back to two stacked lines if the right side is huge
            return self.line(left, bold=bold).line(right_str, align="right", bold=bold)

        left_str = left[: avail - 1] if len(left) > avail - 1 else left
        padding = " " * max(0, avail - len(left_str))
        return self.line(f"{left_str}{padding}{right_str}", bold=bold)

    def three_col(
        self,
        left: str,
        middle: str,
        right: str,
        *,
        widths: tuple[int, int, int] | None = None,
        bold: bool = False,
    ):
        """
        Generic three-column layout (used for line-item rows).
        widths: (left, middle, right). Defaults chosen for 32-char paper.
        """
        if widths is None:
            widths = (self.width - 14, 6, 8)
        lw, mw, rw = widths
        left_s = (left[: lw - 1]).ljust(lw)
        mid_s = middle.rjust(mw)
        right_s = right.rjust(rw)
        return self.line(f"{left_s}{mid_s}{right_s}", bold=bold)

    def wrap(self, text: str, *, indent: int = 0):
        """Word-wrap to receipt width."""
        words = text.split()
        current = " " * indent
        for word in words:
            if len(current) + 1 + len(word) > self.width:
                self.line(current)
                current = " " * indent + word
            else:
                current = current + (" " if current.strip() else "") + word
        if current.strip():
            self.line(current)
        return self

    # ---- QR / barcodes --------------------------------------
    def qr(self, data: str, *, size: int = 6, align: str = "center"):
        """
        ESC/POS QR code — GS ( k store, GS ( k print.
        Size 1..16; 6 is a good default for 58 mm paper.
        """
        payload = data.encode("utf-8")
        data_len = len(payload) + 3
        pL = data_len & 0xFF
        pH = (data_len >> 8) & 0xFF

        self._buffer.append(_align_code(align))
        # Store QR in symbol storage area (model 2)
        self._buffer.append(
            GS + b"(k"
            + bytes([pL, pH, 0x31, 0x50, 0x30])
            + payload
        )
        # Set module size
        self._buffer.append(GS + b"(k" + bytes([0x03, 0x00, 0x31, 0x43, size]))
        # Set error correction level (M)
        self._buffer.append(GS + b"(k" + bytes([0x03, 0x00, 0x31, 0x45, 0x31]))
        # Print the symbol
        self._buffer.append(GS + b"(k" + bytes([0x03, 0x00, 0x31, 0x51, 0x30]))
        self._buffer.append(CMD_LINE_FEED)
        return self

    def barcode(self, data: str, *, barcode_type: str = "CODE128", align: str = "center"):
        """
        ESC/POS barcode — CODE39 / CODE128 / EAN13 supported.
        """
        type_map = {"CODE39": 4, "CODE128": 73, "EAN13": 67, "EAN8": 68, "UPCA": 65}
        bc_type = type_map.get(barcode_type.upper(), 73)
        payload = data.encode("ascii", errors="replace")

        self._buffer.append(_align_code(align))
        # GS h (height) GS w (width) GS H (text position below)
        self._buffer.append(GS + b"h\x50")   # 80 dots tall
        self._buffer.append(GS + b"w\x02")   # width multiplier 2
        self._buffer.append(GS + b"H\x02")   # text below barcode
        # GS k <m> <n> <data>  — m=type, n=len, data
        self._buffer.append(GS + b"k" + bytes([bc_type, len(payload)]) + payload)
        self._buffer.append(CMD_LINE_FEED)
        return self

    # ---- Hardware actions -----------------------------------
    def cut(self, *, partial: bool = True, feed_first: bool = True):
        if feed_first:
            self.feed(3)
        self._buffer.append(CMD_CUT_PARTIAL if partial else CMD_CUT_FULL)
        return self

    def open_drawer(self, pin: int = 0):
        """ESC p m t1 t2 — pin 0 or 1, 0x19 = 50 ms pulse."""
        self._buffer.append(ESC + b"p" + bytes([pin, 0x19, 0xFA]))
        return self

    # ---- Output ---------------------------------------------
    def bytes(self) -> bytes:
        return b"".join(self._buffer)

    def __bytes__(self) -> bytes:
        return self.bytes()


# ---------------------------------------------------------------------------
# Structured receipt builders — consume the payload dicts stored on PrintJob
# ---------------------------------------------------------------------------
def render_sale_receipt(payload: dict, *, paper_width_mm: int = 58) -> bytes:
    """
    payload is the dict produced by SaleService.receipt_payload() (see sales app).
    """
    width = 32 if paper_width_mm <= 58 else 48
    r = ReceiptRenderer(width=width).reset()

    business = payload.get("business", {})
    sale = payload.get("sale", {})
    items = payload.get("items", [])
    payments = payload.get("payments", [])

    # Header
    r.line(business.get("name", "DEMKA"), align="center", bold=True, double_height=True)
    if business.get("address"):
        r.wrap(business["address"], indent=0)
    if business.get("kra_pin"):
        r.line(f"KRA PIN: {business['kra_pin']}", align="center")
    if business.get("phone"):
        r.line(f"Tel: {business['phone']}", align="center")
    r.rule("=")

    # Meta
    r.two_col(f"Receipt: {sale.get('sale_number', '')}", sale.get("created_at", "")[:10])
    if sale.get("agent"):
        r.line(f"Cashier: {sale['agent']}")
    if sale.get("location"):
        r.line(f"Till: {sale['location']}")
    if sale.get("customer_name"):
        r.line(f"Customer: {sale['customer_name']}")
    if sale.get("customer_phone"):
        r.line(f"Phone: {sale['customer_phone']}")
    r.rule()

    # Line items
    r.three_col("Item", "Qty", "Amount", bold=True)
    r.rule()
    for item in items:
        r.three_col(
            item.get("name", "")[:width - 16],
            item.get("quantity", ""),
            item.get("line_total", ""),
        )
    r.rule()

    # Totals
    r.two_col("Subtotal", sale.get("subtotal", "0.00"))
    r.two_col("VAT", sale.get("tax_amount", "0.00"))
    if Decimal(str(sale.get("discount_amount", "0") or "0")) > 0:
        r.two_col("Discount", f"-{sale['discount_amount']}")
    r.two_col("TOTAL", sale.get("total", "0.00"), bold=True)
    if Decimal(str(sale.get("amount_paid", "0") or "0")) > 0:
        r.two_col("Paid", sale.get("amount_paid", "0.00"))
    if Decimal(str(sale.get("balance_due", "0") or "0")) > 0:
        r.two_col("Balance", sale.get("balance_due", "0.00"), bold=True)

    # Payments received
    if payments:
        r.rule()
        r.line("Payments:", bold=True)
        for p in payments:
            r.two_col(f"  {p.get('method', '')} {p.get('reference', '')}".rstrip(),
                      p.get("amount", ""))

    r.rule("=")

    # Footer
    if business.get("receipt_footer"):
        r.line(business["receipt_footer"], align="center")
    r.line("Asante! Karibu tena.", align="center")

    # KRA eTIMS QR
    if sale.get("etims_invoice_number") and payload.get("etims_qr_url"):
        r.newline()
        r.qr(payload["etims_qr_url"])
        r.line(f"eTIMS: {sale['etims_invoice_number']}", align="center")
        r.line("Verify with KRA", align="center")

    r.cut()
    return r.bytes()


def render_credit_note(payload: dict, *, paper_width_mm: int = 58) -> bytes:
    """
    payload keys: business, sales_return, original_sale, items, etims_qr_url
    """
    width = 32 if paper_width_mm <= 58 else 48
    r = ReceiptRenderer(width=width).reset()

    business = payload.get("business", {})
    ret = payload.get("sales_return", {})
    orig = payload.get("original_sale", {})
    items = payload.get("items", [])

    r.line(business.get("name", "DEMKA"), align="center", bold=True, double_height=True)
    r.line("CREDIT NOTE", align="center", bold=True, double_height=True)
    if business.get("kra_pin"):
        r.line(f"KRA PIN: {business['kra_pin']}", align="center")
    r.rule("=")

    r.two_col(f"Credit Note: {ret.get('return_number', '')}",
              ret.get("created_at", "")[:10])
    r.two_col(f"Original: {orig.get('sale_number', '')}", "")
    r.line(f"Customer: {ret.get('customer_name', '')}")
    if ret.get("reason"):
        r.wrap(f"Reason: {ret['reason']}")
    r.rule()

    r.three_col("Item", "Qty", "Amount", bold=True)
    r.rule()
    for item in items:
        r.three_col(
            item.get("name", "")[:width - 16],
            item.get("quantity", ""),
            item.get("line_total", ""),
        )
    r.rule()

    r.two_col("Refund Total", ret.get("refund_amount", "0.00"), bold=True)
    r.two_col("Method", ret.get("refund_method_code", "—"))

    if payload.get("etims_qr_url"):
        r.newline()
        r.qr(payload["etims_qr_url"])
        r.line("KRA eTIMS verified", align="center")

    r.cut()
    return r.bytes()


def render_preorder_slip(payload: dict, *, paper_width_mm: int = 58) -> bytes:
    """Pickup slip printed at the shop for the customer."""
    width = 32 if paper_width_mm <= 58 else 48
    r = ReceiptRenderer(width=width).reset()

    business = payload.get("business", {})
    pre = payload.get("preorder", {})
    items = payload.get("items", [])

    r.line(business.get("name", "DEMKA"), align="center", bold=True, double_height=True)
    r.line("PREORDER SLIP", align="center", bold=True)
    r.rule("=")
    r.two_col(f"Order: {pre.get('preorder_number', '')}",
              pre.get("created_at", "")[:10])
    r.line(f"Customer: {pre.get('customer_name', '')}")
    if pre.get("preferred_pickup_date"):
        r.line(f"Pickup: {pre['preferred_pickup_date']}")
    r.rule()
    r.three_col("Item", "Qty", "Est. Amount", bold=True)
    r.rule()
    for it in items:
        r.three_col(
            it.get("product_name", "")[:width - 16],
            it.get("quantity", ""),
            it.get("line_total", ""),
        )
    r.rule()
    r.two_col("ESTIMATED TOTAL", pre.get("total_estimated", "0.00"), bold=True)
    r.line("Prices finalised at pickup.", align="center")
    r.cut()
    return r.bytes()


def render_route_sheet(payload: dict, *, paper_width_mm: int = 80) -> bytes:
    """Field agent's run sheet — customers to visit, opening cash, van."""
    width = 32 if paper_width_mm <= 58 else 48
    r = ReceiptRenderer(width=width).reset()

    business = payload.get("business", {})
    run = payload.get("run", {})
    customers = payload.get("customers", [])

    r.line(business.get("name", "DEMKA"), align="center", bold=True, double_height=True)
    r.line("ROUTE SHEET", align="center", bold=True)
    r.rule("=")
    r.line(f"Route: {run.get('route_name', '')}")
    r.line(f"Date: {run.get('run_date', '')}")
    r.line(f"Agent: {run.get('agent_name', '')}")
    r.line(f"Van: {run.get('stock_location', '')}")
    r.rule()
    r.line(f"{len(customers)} customers to visit", bold=True)
    r.rule()
    for idx, c in enumerate(customers, start=1):
        r.line(f"{idx}. {c.get('name', '')[:width - 4]}")
        if c.get("phone"):
            r.line(f"   {c['phone']}")
    r.newline()
    r.line("Hand in cash + signed sheet at end of day.", align="center")
    r.cut()
    return r.bytes()


def render_test_slip(printer_name: str, *, paper_width_mm: int = 58) -> bytes:
    r = ReceiptRenderer(width=32 if paper_width_mm <= 58 else 48).reset()
    r.line("DEMKA TEST PRINT", align="center", bold=True, double_height=True)
    r.rule("=")
    r.line(f"Printer: {printer_name}")
    r.line("If you can read this, the printer works.")
    r.line("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", align="center")
    r.line("── ─ ─ ── ─ ─ ──", align="center")
    r.cut()
    return r.bytes()