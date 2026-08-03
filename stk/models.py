from django.db import models
from vault.models import Merchant


class Transaction(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="transactions")
    checkout_request_id = models.CharField(max_length=100, unique=True)
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    customer_phone = models.CharField(max_length=15)
    account_reference = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    result_code = models.IntegerField(blank=True, null=True)
    result_desc = models.CharField(max_length=255, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.checkout_request_id} — {self.status}"