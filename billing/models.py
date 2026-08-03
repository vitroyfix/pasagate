from django.db import models
from vault.models import Merchant


class SubscriptionTier(models.Model):
    """Track 1 pricing tiers — monthly plan with a bundled STK-push allowance."""
    name = models.CharField(max_length=50)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    included_credits = models.PositiveIntegerField()
    overage_rate_per_push = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} — KES {self.monthly_price}/mo, {self.included_credits} pushes"


class MerchantSubscription(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PAST_DUE = "past_due"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAST_DUE, "Past due"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    merchant = models.OneToOneField(Merchant, on_delete=models.CASCADE, related_name="subscription")
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT)
    credits_remaining = models.IntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    renews_at = models.DateTimeField()

    def __str__(self):
        return f"{self.merchant.business_name} on {self.tier.name}"


class MerchantWallet(models.Model):
    """Overage top-up balance — used once tier credits hit zero."""
    merchant = models.OneToOneField(Merchant, on_delete=models.CASCADE, related_name="wallet")
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.merchant.business_name} wallet: KES {self.credit_balance}"


class BillingEvent(models.Model):
    TYPE_SUBSCRIPTION_CHARGE = "SUBSCRIPTION_CHARGE"
    TYPE_CREDIT_CONSUMED = "STK_CREDIT_CONSUMED"
    TYPE_OVERAGE_TOPUP = "OVERAGE_TOPUP"
    TYPE_B2C_COMMISSION = "B2C_COMMISSION"
    TYPE_CHOICES = [
        (TYPE_SUBSCRIPTION_CHARGE, "Subscription charge"),
        (TYPE_CREDIT_CONSUMED, "STK credit consumed"),
        (TYPE_OVERAGE_TOPUP, "Overage top-up"),
        (TYPE_B2C_COMMISSION, "B2C commission"),
    ]

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="billing_events")
    type = models.CharField(max_length=25, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} — {self.merchant.business_name} — KES {self.amount}"
    