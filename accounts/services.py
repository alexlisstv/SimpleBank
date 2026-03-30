from decimal import Decimal

from django.db import transaction

from .fees import compute_transfer_fee
from .models import Account, Transaction


class TransferError(Exception):
    """Domain error for transfer failures (mapped to HTTP in the view)."""


class RecipientNotFound(TransferError):
    pass


class SelfTransferNotAllowed(TransferError):
    pass


class InsufficientFunds(TransferError):
    pass


@transaction.atomic
def execute_transfer(
    *,
    sender: Account,
    recipient_account_number: str,
    amount: Decimal,
) -> tuple[Decimal, Decimal]:
    """
    Debit sender by exactly ``amount`` (gross). Fee is taken from that same sum;
    recipient is credited ``amount - fee``. Sender gets a ``debit`` (principal) and a ``fee`` row.
    """
    if amount < Decimal("0.01"):
        raise TransferError("Transfer amount must be at least 0.01.")

    normalized_to = recipient_account_number.strip()
    if normalized_to == sender.account_number:
        raise SelfTransferNotAllowed()

    recipient_pk = Account.objects.filter(account_number=normalized_to).values_list(
        "pk", flat=True
    ).first()
    if recipient_pk is None:
        raise RecipientNotFound()

    sender_pk = sender.pk
    low_pk, high_pk = sorted((sender_pk, recipient_pk))

    # Lock rows in deterministic order (same for every pair of accounts).
    list(
        Account.objects.select_for_update()
        .filter(pk__in=(low_pk, high_pk))
        .order_by("pk")
    )

    sender_locked = Account.objects.select_for_update().get(pk=sender_pk)
    recipient_locked = Account.objects.select_for_update().get(pk=recipient_pk)

    fee = compute_transfer_fee(amount)
    net_to_recipient = amount - fee
    if net_to_recipient < Decimal("0.01"):
        raise TransferError(
            "Gross amount is too small: after fee, recipient would receive less than 0.01.",
        )

    if sender_locked.balance < amount:
        raise InsufficientFunds()

    Transaction.objects.create(
        account=sender_locked,
        amount=net_to_recipient,
        type=Transaction.Type.DEBIT,
        counterparty_account=recipient_locked,
    )
    Transaction.objects.create(
        account=sender_locked,
        amount=fee,
        type=Transaction.Type.FEE,
        counterparty_account=None,
    )
    Transaction.objects.create(
        account=recipient_locked,
        amount=net_to_recipient,
        type=Transaction.Type.CREDIT,
        counterparty_account=sender_locked,
    )

    sender_locked.balance -= amount
    sender_locked.save(update_fields=["balance"])
    recipient_locked.balance += net_to_recipient
    recipient_locked.save(update_fields=["balance"])

    return fee, net_to_recipient
