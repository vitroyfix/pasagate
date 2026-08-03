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
from billing.services import BillingService, InsufficientCreditsError

logger = logging.getLogger(__name__)


class DashboardSTKPushView(APIView):
    """POST /api/stk/push/<merchant_id>/ — you (dashboard) trigger a push for a customer."""
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

        try:
            BillingService.charge_for_push(merchant, checkout_request_id="pending")
        except InsufficientCreditsError as e:
            return Response({"error": str(e)}, status=402)

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


class STKCallbackView(APIView):
    """POST /api/stk/callback/ — Safaricom hits this with the result of every push."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        body = request.data.get("Body", {}).get("stkCallback", {})
        checkout_id = body.get("CheckoutRequestID")
        result_code = body.get("ResultCode")
        result_desc = body.get("ResultDesc")

        try:
            txn = Transaction.objects.get(
                checkout_request_id=checkout_id, status=Transaction.STATUS_PENDING
            )
        except Transaction.DoesNotExist:
            logger.warning("Callback for unknown/non-pending CheckoutRequestID: %s", checkout_id)
            return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

        txn.result_code = result_code
        txn.result_desc = result_desc

        if result_code == 0:
            txn.status = Transaction.STATUS_SUCCESS
            items = {
                item["Name"]: item.get("Value")
                for item in body.get("CallbackMetadata", {}).get("Item", [])
            }
            txn.mpesa_receipt_number = items.get("MpesaReceiptNumber")
        else:
            txn.status = Transaction.STATUS_FAILED

        txn.save()
        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


class TransactionStatusView(APIView):
    """GET /api/stk/status/<checkout_request_id>/ — poll for the result."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, checkout_request_id):
        try:
            txn = Transaction.objects.get(checkout_request_id=checkout_request_id)
        except Transaction.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        return Response({
            "status": txn.status,
            "mpesa_receipt_number": txn.mpesa_receipt_number,
            "result_desc": txn.result_desc,
        })