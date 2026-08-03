import secrets
from rest_framework import serializers
from vault.models import Merchant


class MerchantRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles onboarding for BOTH tracks. `passkey` is write-only —
    accepted on input, encrypted immediately, NEVER echoed back.
    """

    passkey = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Merchant
        fields = [
            "id", "business_name", "settlement_type", "shortcode",
            "account_ref_format", "passkey", "payout_phone_number",
            "api_public_key", "allowed_domain", "webhook_url", "created_at",
        ]
        read_only_fields = ["id", "api_public_key", "created_at"]

    def validate(self, data):
        settlement_type = data.get("settlement_type")

        if settlement_type == Merchant.SETTLEMENT_DIRECT:
            if not data.get("shortcode") or not data.get("passkey"):
                raise serializers.ValidationError(
                    "Direct settlement requires both 'shortcode' and 'passkey'."
                )
        elif settlement_type == Merchant.SETTLEMENT_CUSTODIAL:
            phone = data.get("payout_phone_number")
            if not phone:
                raise serializers.ValidationError(
                    "Custodial settlement requires 'payout_phone_number'."
                )
            if not (phone.startswith("254") and len(phone) == 12 and phone.isdigit()):
                raise serializers.ValidationError(
                    "payout_phone_number must be in format 254XXXXXXXXX."
                )
        return data

    def create(self, validated_data):
        raw_passkey = validated_data.pop("passkey", None)
        validated_data["api_public_key"] = f"pk_live_{secrets.token_hex(20)}"
        validated_data["owner"] = self.context["request"].user

        merchant = Merchant(**validated_data)
        if raw_passkey:
            merchant.passkey = raw_passkey  # triggers encryption via the setter
        merchant.save()
        return merchant


class MerchantPublicSerializer(serializers.ModelSerializer):
    """Safe-to-return view — used everywhere credentials must never leak."""

    class Meta:
        model = Merchant
        fields = [
            "id", "business_name", "settlement_type", "api_public_key",
            "allowed_domain", "is_active", "created_at",
        ]