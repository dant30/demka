from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.preorders.models import PreorderCustomerSession


@override_settings(CACHES={
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "preorder-portal-auth-tests",
    },
})
class PortalAuthTests(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
        )
        # Clean up rate-limit cache between tests
        from django.core.cache import cache
        cache.clear()

    @patch("apps.preorders.services.auth_service.SmsService.send")
    def test_request_otp_creates_session(self, mock_send):
        res = self.client.post(
            "/api/preorders/portal/auth/request-otp/",
            {"phone": "0744444444"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            PreorderCustomerSession.objects.filter(customer=self.customer).count(), 1,
        )
        session = PreorderCustomerSession.objects.get()
        self.assertFalse(session.is_active)
        self.assertNotEqual(session.otp_code, "123456")  # hashed

    def test_request_otp_unknown_phone_returns_same_body(self):
        res = self.client.post(
            "/api/preorders/portal/auth/request-otp/",
            {"phone": "0799999999"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("If the phone is registered", res.data["detail"])

    @patch("apps.preorders.services.auth_service.SmsService.send")
    def test_request_otp_retail_customer_silently_ignored(self, mock_send):
        Customer.objects.create(
            code="CUST-9999", name="Retail",
            phone="0755555555", customer_type="RETAIL",
        )
        mock_send.reset_mock()
        res = self.client.post(
            "/api/preorders/portal/auth/request-otp/",
            {"phone": "0755555555"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(PreorderCustomerSession.objects.count(), 0)
        mock_send.assert_not_called()

    @patch("apps.preorders.services.auth_service.SmsService.send")
    def test_verify_otp_activates_session(self, mock_send):
        from django.contrib.auth.hashers import make_password
        from django.utils import timezone
        from datetime import timedelta

        otp = "123456"
        PreorderCustomerSession.objects.create(
            customer=self.customer,
            otp_code=make_password(otp),
            otp_expires_at=timezone.now() + timedelta(minutes=5),
            session_token="tok-abc",
        )
        res = self.client.post(
            "/api/preorders/portal/auth/verify-otp/",
            {"phone": "0744444444", "otp": otp},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["session_token"], "tok-abc")
        session = PreorderCustomerSession.objects.get()
        self.assertTrue(session.is_active)

    @patch("apps.preorders.services.auth_service.SmsService.send")
    def test_wrong_otp_increments_attempts(self, mock_send):
        from django.contrib.auth.hashers import make_password
        from django.utils import timezone
        from datetime import timedelta

        PreorderCustomerSession.objects.create(
            customer=self.customer,
            otp_code=make_password("123456"),
            otp_expires_at=timezone.now() + timedelta(minutes=5),
            session_token="tok-abc",
        )
        res = self.client.post(
            "/api/preorders/portal/auth/verify-otp/",
            {"phone": "0744444444", "otp": "999999"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        session = PreorderCustomerSession.objects.get()
        self.assertEqual(session.attempts, 1)
        self.assertFalse(session.is_active)

    @patch("apps.preorders.services.auth_service.SmsService.send")
    def test_locked_after_max_attempts(self, mock_send):
        from django.contrib.auth.hashers import make_password
        from django.utils import timezone
        from datetime import timedelta

        PreorderCustomerSession.objects.create(
            customer=self.customer,
            otp_code=make_password("123456"),
            otp_expires_at=timezone.now() + timedelta(minutes=5),
            session_token="tok-abc",
            attempts=5,
        )
        res = self.client.post(
            "/api/preorders/portal/auth/verify-otp/",
            {"phone": "0744444444", "otp": "123456"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)