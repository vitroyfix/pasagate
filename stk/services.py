import base64
import datetime
import requests
from decouple import config
from django.core.cache import cache
from vault.models import Merchant


class DarajaAuthError(Exception):
    pass


class DarajaClient:
    """
    Wraps Safaricom Daraja API calls. ONE set of Consumer Key/Secret
    (your platform's own app) authenticates every request, for every
    merchant. What varies per-merchant is the Shortcode + Passkey used
    to build the STK password — that's what determines which till
    actually receives the payment.
    """

    def __init__(self):
        self.env = config("DARAJA_ENV", default="sandbox")
        self.base_url = (
            "https://sandbox.safaricom.co.ke" if self.env == "sandbox"
            else "https://api.safaricom.co.ke"
        )
        self.consumer_key = config("DARAJA_CONSUMER_KEY")
        self.consumer_secret = config("DARAJA_CONSUMER_SECRET")

    def _get_access_token(self) -> str:
        """
        OAuth tokens last ~1hr. Cache in Redis so we're not re-authenticating
        with Safaricom on every single push — this cache key isn't merchant-
        specific since the Consumer Key/Secret is shared across all of them.
        """
        cached = cache.get("daraja_access_token")
        if cached:
            return cached

        resp = requests.get(
            f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
            auth=(self.consumer_key, self.consumer_secret),
            timeout=15,
        )
        if resp.status_code != 200:
            raise DarajaAuthError(f"Failed to obtain Daraja token: {resp.text}")

        token = resp.json()["access_token"]
        cache.set("daraja_access_token", token, timeout=55 * 60)  # 5 min safety margin
        return token

    def _build_password(self, shortcode: str, passkey: str, timestamp: str) -> str:
        raw = f"{shortcode}{passkey}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    def stk_push(self, merchant: Merchant, phone: str, amount: int, callback_url: str,
                 account_reference: str = None, transaction_desc: str = "Payment"):
        token = self._get_access_token()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Direct-track merchants use THEIR OWN shortcode + passkey — this is
        # what makes Safaricom route the payment to their till, not yours.
        shortcode = merchant.shortcode
        passkey = merchant.passkey  # decrypted automatically via the model property
        ref = account_reference or merchant.account_ref_format or merchant.business_name

        password = self._build_password(shortcode, passkey, timestamp)

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": ref,
            "TransactionDesc": transaction_desc,
        }

        resp = requests.post(
            f"{self.base_url}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


daraja = DarajaClient()