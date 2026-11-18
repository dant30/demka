from unittest.mock import patch

from django.test import TestCase

from apps.etims.models import EtimsConfig
from apps.etims.services.client import (
    EtimsClient, EtimsRejection, EtimsTransientError,
)


class ClientTests(TestCase):
    def setUp(self):
        self.cfg = EtimsConfig.get_solo()
        self.cfg.tin = "P051234567A"
        self.cfg.bhf_id = "00"
        self.cfg.device_serial = "DEV-1"
        self.cfg.cmc_key = "KEY-ABC"
        self.cfg.environment = EtimsConfig.Environment.SANDBOX
        self.cfg.save()
        self.client = EtimsClient(self.cfg)

    def test_headers_carry_tin_bhfid_cmckey(self):
        h = self.client._headers()
        self.assertEqual(h["tin"], "P051234567A")
        self.assertEqual(h["bhfId"], "00")
        self.assertEqual(h["cmcKey"], "KEY-ABC")

    @patch("apps.etims.services.client.requests.Session.post")
    def test_success_000(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "resultCd": "000", "resultMsg": "Successful",
            "data": {"curRcptNo": 87, "totRcptNo": 1042, "intrlData": "INTRL",
                     "rcptSign": "SIGN", "sdcDateTime": "20260101120000"},
        }
        body = self.client.save_sale({"x": 1})
        self.assertEqual(body["resultCd"], "000")

    @patch("apps.etims.services.client.requests.Session.post")
    def test_validation_9xx_raises_rejection(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "resultCd": "921", "resultMsg": "Duplicate invoice number",
        }
        with self.assertRaises(EtimsRejection):
            self.client.save_sale({"x": 1})

    @patch("apps.etims.services.client.requests.Session.post")
    def test_5xx_raises_transient(self, mock_post):
        mock_post.return_value.status_code = 503
        with self.assertRaises(EtimsTransientError):
            self.client.save_sale({"x": 1})