from django.db import models
from django.conf import settings
from vault.encryption import vault


class Merchant(models.Model):
    SETTLEMENT_DIRECT = "DIRECT"
    SETTLEMENT_CUSTODIAL = "CUSTODIAL_B2C"
    SETTLEMENT_CHOICES = [
        (SETTLEMENT_DIRECT, "Direct to merchant paybill/till"),
        (SETTLEMENT_CUSTODIAL, "Custodial — payout via B2C"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="merchants"
    )
    business_name = models.CharField(max_length=255)
    settlement_type = models.CharField(max_length=20, choices=SETTLEMENT_CHOICES)

    # Track 1 (Direct) fields — null for custodial merchants
    shortcode = models.CharField(max_length=20, blank=True, null=True)
    account_ref_format = models.CharField(max_length=100, blank=True, null=True)
    _passkey_encrypted = models.TextField(blank=True, null=True, db_column="passkey_encrypted")

    # Track 2 (Custodial) fields — null for direct merchants
    payout_phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Widget/API auth
    api_public_key = models.CharField(max_length=64, unique=True)
    allowed_domain = models.CharField(max_length=255, blank=True, null=True)

    webhook_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    @property
    def passkey(self):
        """Decrypts on read — nowhere else in the codebase touches _passkey_encrypted directly."""
        if not self._passkey_encrypted:
            return None
        return vault.decrypt(self._passkey_encrypted)

    @passkey.setter
    def passkey(self, raw_value: str):
        """Encrypts on write — merchant.passkey = 'xyz' never stores plaintext."""
        self._passkey_encrypted = vault.encrypt(raw_value)

    def __str__(self):
        return f"{self.business_name} ({self.settlement_type})"