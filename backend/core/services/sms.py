"""SMS dispatch wrapper for OTS with a console fallback for development."""
import requests
from django.conf import settings


class SmsError(Exception):
    pass


class SmsService:
    @staticmethod
    def send(phone: str, message: str) -> dict:
        provider = settings.SMS_PROVIDER
        if provider == "console":
            print(f"[SMS] to={phone} body={message}")
            return {"status": "console", "phone": phone}
        if provider == "ots":
            if not settings.SMS_ENABLED:
                raise SmsError("SMS delivery is disabled.")
            return SmsService._ots(phone, message)
        raise SmsError(f"Unsupported SMS provider: {provider}")

    @staticmethod
    def send_templated(phone: str, template: str, context: dict) -> dict:
        return SmsService.send(phone, template.format(**context))

    @staticmethod
    def _ots(phone: str, message: str) -> dict:
        token = settings.SMS_API_TOKEN.strip()
        sender_id = settings.SMS_SENDER_ID.strip()
        missing = [
            name for name, value in (
                ("SMS_API_TOKEN", token),
                ("SMS_SENDER_ID", sender_id),
            ) if not value
        ]
        if missing:
            raise SmsError(f"SMS provider is missing configuration: {', '.join(missing)}.")

        base_url = settings.SMS_API_BASE_URL.rstrip("/")
        send_path = settings.SMS_API_SEND_PATH.strip("/")
        url = f"{base_url}/{send_path}"
        payload = {
            "recipient": SmsService._normalize_kenyan_phone(phone),
            "sender_id": sender_id,
            "type": "plain",
            "message": message,
        }

        try:
            response = requests.post(
                url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=settings.SMS_API_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise SmsError("OTS SMS provider could not be reached.") from exc

        if not 200 <= response.status_code < 300:
            raise SmsError(f"OTS SMS provider returned HTTP {response.status_code}.")

        try:
            return response.json()
        except ValueError:
            return {"status": "sent", "recipient": payload["recipient"]}

    @staticmethod
    def _normalize_kenyan_phone(phone: str) -> str:
        value = "".join(
            character for character in str(phone).strip()
            if character.isdigit() or character == "+"
        )
        if value.startswith("+254"):
            return value[1:]
        if value.startswith("254"):
            return value
        if value.startswith("0") and len(value) == 10:
            return f"254{value[1:]}"
        return value