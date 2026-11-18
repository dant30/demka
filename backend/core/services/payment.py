"""M-Pesa Daraja API wrapper: STK Push, status query, callback processing."""
import base64
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone


class MpesaError(Exception):
    def __init__(self, message, payload=None):
        self.payload = payload or {}
        super().__init__(message)


class MpesaService:
    @staticmethod
    def _base_url() -> str:
        return (
            "https://api.safaricom.co.ke"
            if settings.MPESA["ENVIRONMENT"] == "production"
            else "https://sandbox.safaricom.co.ke"
        )

    @classmethod
    def _password(cls, ts: str) -> str:
        sc = settings.MPESA["SHORTCODE"]
        pk = settings.MPESA["PASSKEY"]
        return base64.b64encode(f"{sc}{pk}{ts}".encode()).decode()

    @classmethod
    def get_access_token(cls) -> str:
        key = settings.MPESA["CONSUMER_KEY"]
        secret = settings.MPESA["CONSUMER_SECRET"]
        auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
        r = requests.get(
            f"{cls._base_url()}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {auth}"},
            timeout=15,
        )
        if r.status_code != 200:
            raise MpesaError("Failed to fetch access token.", r.json())
        return r.json()["access_token"]

    @classmethod
    def stk_push(cls, phone: str, amount: float, account_ref: str) -> dict:
        token = cls.get_access_token()
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "BusinessShortCode": settings.MPESA["SHORTCODE"],
            "Password": cls._password(ts),
            "Timestamp": ts,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": settings.MPESA["SHORTCODE"],
            "PhoneNumber": phone,
            "CallBackURL": settings.MPESA["CALLBACK_URL"],
            "AccountReference": account_ref,
            "TransactionDesc": f"Payment {account_ref}",
        }
        r = requests.post(
            f"{cls._base_url()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        data = r.json()
        if r.status_code != 200:
            raise MpesaError(data.get("errorMessage", "STK push failed."), data)
        return data

    @classmethod
    def query_status(cls, checkout_request_id: str) -> dict:
        token = cls.get_access_token()
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        payload = {
            "BusinessShortCode": settings.MPESA["SHORTCODE"],
            "Password": cls._password(ts),
            "Timestamp": ts,
            "CheckoutRequestID": checkout_request_id,
        }
        r = requests.post(
            f"{cls._base_url()}/mpesa/stkpushquery/v1/query",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        return r.json()


class MpesaCallbackProcessor:
    """Persist a C2B callback into MpesaTransaction for later reconciliation."""

    @staticmethod
    def process(payload: dict) -> dict:
        from apps.payments.models import MpesaTransaction

        stk = payload.get("Body", {}).get("stkCallback", {})
        if stk.get("ResultCode") != 0:
            return {"matched": False, "reason": stk.get("ResultDesc", "Not successful")}

        meta = {
            i["Name"]: i.get("Value")
            for i in stk.get("CallbackMetadata", {}).get("Item", [])
        }
        receipt = meta.get("MpesaReceiptNumber", "")
        tx, _ = MpesaTransaction.objects.update_or_create(
            transaction_id=stk.get("CheckoutRequestID", receipt),
            defaults={
                "mpesa_receipt": receipt,
                "phone": str(meta.get("PhoneNumber", "")),
                "amount": meta.get("Amount", 0),
                "transaction_date": timezone.now(),
                "raw_payload": payload,
            },
        )
        return {"matched": True, "transaction_id": tx.transaction_id, "receipt": receipt}