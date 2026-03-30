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
