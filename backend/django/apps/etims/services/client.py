"""
Thin HTTP transport for the KRA OSCU JSON API.

No OAuth. Every request carries tin / bhfId / cmcKey headers.
resultCd is a STRING. "000" = success, "001" = general failure, 9xx = validation.
"""
import logging

import requests

logger = logging.getLogger(__name__)


class EtimsError(Exception):
    """Base for all eTIMS client errors."""


class EtimsTransientError(EtimsError):
    """Retryable — network, 5xx, KRA maintenance."""


class EtimsRejection(EtimsError):
    """Non-retryable — KRA returned a validation rejection."""

    def __init__(self, result_cd: str, result_msg: str, raw: dict):
        self.result_cd = result_cd
        self.result_msg = result_msg
        self.raw = raw
        super().__init__(f"KRA rejection {result_cd}: {result_msg}")


SUCCESS_CODES = {"0", "00", "000", "0000", "001"}


class EtimsClient:
    def __init__(self, config, *, timeout: int = 30):
        self.config = config
        self.timeout = timeout
        self.base_url = config.base_url
        self.session = requests.Session()

    # ---- Header builder -----------------------------------
    def _headers(self) -> dict:
        return {
            "tin": self.config.tin,
            "bhfId": self.config.bhf_id,
            "cmcKey": self.config.cmc_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ---- Core transport -----------------------------------
    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.post(
                url, json=payload, headers=self._headers(), timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise EtimsTransientError(f"Network error calling {path}: {exc}") from exc

        if resp.status_code >= 500:
            raise EtimsTransientError(
                f"KRA server error {resp.status_code} on {path}",
            )
        if resp.status_code >= 400:
            raise EtimsRejection(
                str(resp.status_code), resp.text[:500], {"http_status": resp.status_code},
            )

        try:
            body = resp.json()
        except ValueError as exc:
            raise EtimsTransientError(f"Non-JSON response on {path}") from exc

        logger.info("eTIMS %s → %s", path, body.get("resultCd"))
        return body

    # ---- Public API ---------------------------------------
    def initialize_device(self) -> dict:
        """POST /selectInitOsdcInfo — one-time per branch."""
        body = self._post(
            "/selectInitOsdcInfo",
            {
                "tin": self.config.tin,
                "bhfId": self.config.bhf_id,
                "dvcSrlNo": self.config.device_serial,
            },
        )
        self._raise_if_rejected(body, context="selectInitOsdcInfo")
        return body.get("data", {}).get("info", {})

    def select_code_list(self, last_req_dt: str = "20200101000000") -> dict:
        body = self._post(
            "/selectCodeList",
            {"tin": self.config.tin, "bhfId": self.config.bhf_id, "lastReqDt": last_req_dt},
        )
        self._raise_if_rejected(body, context="selectCodeList")
        return body.get("data", {})

    def select_item_cls_list(self, last_req_dt: str = "20200101000000") -> dict:
        body = self._post(
            "/selectItemClsList",
            {"tin": self.config.tin, "bhfId": self.config.bhf_id, "lastReqDt": last_req_dt},
        )
        self._raise_if_rejected(body, context="selectItemClsList")
        return body.get("data", {})

    def save_item(self, payload: dict) -> dict:
        body = self._post("/saveItem", payload)
        self._raise_if_rejected(body, context="saveItem")
        return body

    def save_sale(self, payload: dict) -> dict:
        body = self._post("/saveTrnsSalesOsdc", payload)
        self._raise_if_rejected(body, context="saveTrnsSalesOsdc")
        return body

    def select_notice_list(self, last_req_dt: str = "20200101000000") -> dict:
        body = self._post(
            "/selectNoticeList",
            {"tin": self.config.tin, "bhfId": self.config.bhf_id, "lastReqDt": last_req_dt},
        )
        self._raise_if_rejected(body, context="selectNoticeList")
        return body.get("data", {})

    # ---- Error interpretation -----------------------------
    @staticmethod
    def _raise_if_rejected(body: dict, *, context: str) -> None:
        result_cd = str(body.get("resultCd", ""))
        if result_cd in SUCCESS_CODES:
            return
        # 9xx = validation, do not retry
        if result_cd.isdigit() and 900 <= int(result_cd) < 1000:
            raise EtimsRejection(
                result_cd, body.get("resultMsg", "Validation failed"), body,
            )
        # Everything else: retry
        raise EtimsTransientError(
            f"{context} failed {result_cd}: {body.get('resultMsg', '')}",
        )