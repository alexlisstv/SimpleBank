from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Account(models.Model):
    """User-owned account with a unique 10-digit number and Decimal balance."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account",
    )
    account_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\d{10}$",
                message="Account number must be exactly 10 digits.",
            ),
        ],
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        ordering = ["account_number"]

    def __str__(self) -> str:
        return f"{self.account_number} ({self.user.email})"


class Transaction(models.Model):
    """Ledger line: positive amount with credit/debit direction."""

    class Type(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    # Set on transfer-related rows when the counterparty account is known (phase 5).
    counterparty_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counterparty_transactions",
    )

    class Meta:
        ordering = ["-timestamp", "-pk"]
        indexes = [
            models.Index(fields=["account", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} {self.amount} @ {self.account_id}"
