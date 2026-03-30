import secrets
from decimal import Decimal

from django.db import IntegrityError, transaction

from accounts.constants import WELCOME_CREDIT_AMOUNT
from accounts.models import Account, Transaction

from .models import User

_MAX_ACCOUNT_NUMBER_ATTEMPTS = 64


def _random_account_number() -> str:
    return f"{secrets.randbelow(10**10):010d}"


@transaction.atomic
def register_user_with_account(*, email: str, password: str) -> tuple[User, Account]:
    """
    Create user, unique account, welcome credit ledger row, and balance in one DB transaction.
    Retries account number generation on rare collisions.
    """
    user = User.objects.create_user(email=email, password=password)
    account = None
    for _ in range(_MAX_ACCOUNT_NUMBER_ATTEMPTS):
        number = _random_account_number()
        try:
            account = Account.objects.create(
                user=user,
                account_number=number,
                balance=Decimal("0.00"),
            )
            break
        except IntegrityError:
            continue
    if account is None:
        raise RuntimeError("Could not allocate a unique account number")

    Transaction.objects.create(
        account=account,
        amount=WELCOME_CREDIT_AMOUNT,
        type=Transaction.Type.CREDIT,
    )
    account.balance = WELCOME_CREDIT_AMOUNT
    account.save(update_fields=["balance"])
    return user, account
