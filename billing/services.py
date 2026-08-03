from decimal import Decimal
from django.db import transaction as db_transaction
from billing.models import MerchantSubscription, MerchantWallet, BillingEvent
from vault.models import Merchant


class InsufficientCreditsError(Exception):
    pass


class BillingService:
    """
    All STK-push billing logic lives here, separate from stk/ — the
    orchestration code just calls into this without needing to know
    HOW billing math works internally.
    """

    @staticmethod
    @db_transaction.atomic
    def charge_for_push(merchant: Merchant, checkout_request_id: str):
        """
        Called BEFORE an STK push is sent. Consumes 1 subscription credit;
        falls back to wallet overage rate if tier credits are exhausted.
        Raises InsufficientCreditsError if neither is available.
        """
        sub = MerchantSubscription.objects.select_for_update().get(merchant=merchant)

        if sub.credits_remaining > 0:
            sub.credits_remaining -= 1
            sub.save(update_fields=["credits_remaining"])
            BillingEvent.objects.create(
                merchant=merchant,
                type=BillingEvent.TYPE_CREDIT_CONSUMED,
                amount=Decimal("0.00"),
                transaction_reference=checkout_request_id,
            )
            return

        wallet, _ = MerchantWallet.objects.select_for_update().get_or_create(merchant=merchant)
        overage_rate = sub.tier.overage_rate_per_push
        if wallet.credit_balance < overage_rate:
            raise InsufficientCreditsError(
                f"{merchant.business_name} has no subscription credits and insufficient wallet balance."
            )

        wallet.credit_balance -= overage_rate
        wallet.save(update_fields=["credit_balance"])
        BillingEvent.objects.create(
            merchant=merchant,
            type=BillingEvent.TYPE_OVERAGE_TOPUP,
            amount=overage_rate,
            transaction_reference=checkout_request_id,
        )