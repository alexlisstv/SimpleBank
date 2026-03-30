from decimal import Decimal

from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import Account, Transaction


class BalanceSerializer(serializers.ModelSerializer):
    """Expose balance as a decimal string in JSON (no float)."""

    balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True,
    )

    class Meta:
        model = Account
        fields = ("balance",)


class AccountNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("account_number",)
        read_only_fields = fields


class TransactionListSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        coerce_to_string=True,
        read_only=True,
    )

    class Meta:
        model = Transaction
        fields = ("amount", "type", "timestamp")
        read_only_fields = fields


class TransferSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    to_account_number = serializers.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="Recipient account number must be exactly 10 digits.",
            ),
        ],
    )


class TransferResponseSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    fee = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    recipient_receives = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    recipient_account_number = serializers.CharField()
