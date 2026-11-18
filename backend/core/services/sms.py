"""SMS dispatch wrapper (Africa's Talking + console fallback for dev)."""
import requests
from django.conf import settings


class SmsError(Exception):
    pass


class SmsService:
    @staticmethod
    def send(phone: str, message: str) -> dict:
        provider = settings.SMS["PROVIDER"]
        if provider == "africastalking":
            return SmsService._africastalking(phone, message)
        if provider == "console":
            print(f"[SMS] to={phone} body={message}")
            return {"status": "console", "phone": phone}
        raise SmsError(f"Unsupported SMS provider: {provider}")

    @staticmethod
    def send_templated(phone: str, template: str, context: dict) -> dict:
        return SmsService.send(phone, template.format(**context))

    @staticmethod
    def _africastalking(phone: str, message: str) -> dict:
        r = requests.post(
            "https://api.africastalking.com/version1/messaging",
            headers={
                "apiKey": settings.SMS["API_KEY"],
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "username": settings.SMS["USERNAME"],
                "to": phone,
                "message": message,
                "from": settings.SMS.get("SENDER_ID", ""),
            },
            timeout=15,
        )
        if r.status_code >= 400:
            raise SmsError(f"SMS failed: {r.status_code} {r.text}")
        return r.json()