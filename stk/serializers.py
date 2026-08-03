from rest_framework import serializers


class STKPushRequestSerializer(serializers.Serializer):
    phone = serializers.RegexField(
        regex=r"^254\d{9}$",
        error_messages={"invalid": "phone must be in format 254XXXXXXXXX"},
    )
    amount = serializers.IntegerField(min_value=1)
    account_reference = serializers.CharField(required=False, allow_blank=True)
    transaction_desc = serializers.CharField(required=False, default="Payment")