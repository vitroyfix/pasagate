import logging
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from vault.models import Merchant
from vault.permissions import IsMerchantOwner
from stk.models import Transaction
from stk.serializers import STKPushRequestSerializer
from stk.services import daraja
from billing.services import BillingService, InsufficientCreditsError  # NEW

logger = logging.getLogger(__name__)


class DashboardSTKPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, merchant_id):
        merchant = Merchant.objects.get(pk=merchant_id)
        if not IsMerchantOwner().has_object_permission(request, self, merchant):
            self.permission_denied(request)

        if not merchant.is_active:
            return Response({"error": "Merchant account is not active"}, status=403)

        serializer = STKPushRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # NEW — bill BEFORE spending money/effort calling Safaricom.
        # We don't have a checkout_request_id yet at this point (Safaricom
        # hasn't responded), so we bill against a placeholder reference —
        # good enough for the ledger, since the real link is the merchant + timestamp.
        try:
            BillingService.charge_for_push(merchant, checkout_request_id="pending")
        except InsufficientCreditsError as e:
            return Response({"error": str(e)}, status=402)  # 402 Payment Required

        callback_url = f"{settings.PUBLIC_BASE_URL}/api/stk/callback/"

        try:
            daraja_response = daraja.stk_push(
                merchant=merchant,
                phone=data["phone"],
                amount=data["amount"],
                callback_url=callback_url,
                account_reference=data.get("account_reference"),
                transaction_desc=data.get("transaction_desc", "Payment"),
            )
        except Exception as exc:
            logger.exception("STK push failed for merchant %s", merchant.id)
            return Response({"error": "Failed to initiate STK push", "detail": str(exc)}, status=502)

        checkout_id = daraja_response.get("CheckoutRequestID")
        if not checkout_id:
            return Response({"error": "Unexpected Daraja response", "raw": daraja_response}, status=502)

        Transaction.objects.create(
            merchant=merchant,
            checkout_request_id=checkout_id,
            merchant_request_id=daraja_response.get("MerchantRequestID"),
            amount=data["amount"],
            customer_phone=data["phone"],
            account_reference=data.get("account_reference"),
        )

        return Response(
            {"status": "STK push sent", "checkout_request_id": checkout_id},
            status=status.HTTP_202_ACCEPTED,
        )