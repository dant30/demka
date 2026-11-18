"""Build the KRA verification URL that goes into the printed QR code."""
from urllib.parse import quote


def build_qr_url(*, tin: str, bhf_id: str, rcpt_sign: str, sandbox: bool = False) -> str:
    host = "etims-sbx.kra.go.ke" if sandbox else "etims.kra.go.ke"
    data = quote(f"{tin}{bhf_id}{rcpt_sign}")
    return (
        f"https://{host}/common/link/etims/receipt/"
        f"indexEtimsReceiptData?Data={data}"
    )