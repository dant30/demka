from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from core.services.sms import SmsError, SmsService


@override_settings(
    SMS_PROVIDER="ots",
    SMS_ENABLED=True,
    SMS_API_BASE_URL="https://sms.ots.co.ke/api/v3/",
    SMS_API_SEND_PATH="sms/send",
    SMS_API_TOKEN="test-token",
    SMS_SENDER_ID="DEMKA",
    SMS_API_TIMEOUT_SECONDS=8,
)
class SmsServiceTests(SimpleTestCase):
    @patch("core.services.sms.requests.post")
    def test_send_ots_normalizes_phone_and_uses_configured_contract(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {"status": "success"}
        post.return_value = response

        result = SmsService.send("+254 712 345 678", "Your code is 123456")

        self.assertEqual(result, {"status": "success"})
        post.assert_called_once_with(
            "https://sms.ots.co.ke/api/v3/sms/send",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json",
            },
            json={
                "recipient": "254712345678",
                "sender_id": "DEMKA",
                "type": "plain",
                "message": "Your code is 123456",
            },
            timeout=8,
        )

    @override_settings(SMS_ENABLED=False)
    @patch("core.services.sms.requests.post")
    def test_disabled_sms_does_not_call_provider(self, post):
        with self.assertRaisesMessage(SmsError, "SMS delivery is disabled."):
            SmsService.send("0712345678", "Hello")

        post.assert_not_called()

    @patch("core.services.sms.requests.post")
    def test_provider_http_error_does_not_expose_response_body(self, post):
        post.return_value = Mock(status_code=401, text="sensitive provider response")

        with self.assertRaisesMessage(SmsError, "OTS SMS provider returned HTTP 401."):
            SmsService.send("0712345678", "Hello")