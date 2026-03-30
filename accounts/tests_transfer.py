import threading
from decimal import Decimal

from django.db import close_old_connections
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.constants import WELCOME_CREDIT_AMOUNT
from accounts.fees import compute_transfer_fee
from accounts.models import Account, Transaction
from users.models import User


class TransferFeeTests(TransactionTestCase):
    def test_fee_uses_minimum_when_percent_is_lower(self):
        self.assertEqual(compute_transfer_fee(Decimal("100.00")), Decimal("5.00"))

    def test_fee_uses_percent_when_higher_than_minimum(self):
        self.assertEqual(compute_transfer_fee(Decimal("1000.00")), Decimal("25.00"))

    def test_fee_quantizes_half_up(self):
        self.assertEqual(compute_transfer_fee(Decimal("333.00")), Decimal("8.33"))


class TransferAPITests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.register_url = reverse("auth-register")
        self.transfer_url = reverse("transfer-create")
        self.password = "Str0ng!pass_for_tests"
        c = APIClient()
        r1 = c.post(
            self.register_url,
            {"email": "alice@example.com", "password": self.password},
            format="json",
        )
        r2 = c.post(
            self.register_url,
            {"email": "bob@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        self.alice = User.objects.get(email="alice@example.com")
        self.bob = User.objects.get(email="bob@example.com")
        self.alice_account = Account.objects.get(user=self.alice)
        self.bob_account = Account.objects.get(user=self.bob)
        self.bob_number = self.bob_account.account_number
        token = RefreshToken.for_user(self.alice)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_transfer_moves_funds_and_records_ledger(self):
        amount = Decimal("100.00")
        fee = compute_transfer_fee(amount)
        net = amount - fee
        r = self.client.post(
            self.transfer_url,
            {"amount": str(amount), "to_account_number": self.bob_number},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED, r.data)
        self.assertEqual(r.data["amount"], str(amount))
        self.assertEqual(r.data["fee"], str(fee))
        self.assertEqual(r.data["recipient_receives"], str(net))
        self.assertEqual(r.data["recipient_account_number"], self.bob_number)

        self.alice_account.refresh_from_db()
        self.bob_account.refresh_from_db()
        self.assertEqual(self.alice_account.balance, WELCOME_CREDIT_AMOUNT - amount)
        self.assertEqual(self.bob_account.balance, WELCOME_CREDIT_AMOUNT + net)

        principal = Transaction.objects.get(
            account=self.alice_account,
            type=Transaction.Type.DEBIT,
        )
        self.assertEqual(principal.amount, net)
        self.assertEqual(principal.counterparty_account_id, self.bob_account.pk)

        fee_row = Transaction.objects.get(
            account=self.alice_account,
            type=Transaction.Type.FEE,
        )
        self.assertEqual(fee_row.amount, fee)
        self.assertIsNone(fee_row.counterparty_account_id)

        transfer_credit = Transaction.objects.filter(
            account=self.bob_account,
            type=Transaction.Type.CREDIT,
            amount=net,
        ).get()
        self.assertEqual(transfer_credit.counterparty_account_id, self.alice_account.pk)

    def test_transfer_recipient_not_found(self):
        r = self.client.post(
            self.transfer_url,
            {"amount": "10.00", "to_account_number": "0000000000"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_transfer_self_forbidden(self):
        r = self.client.post(
            self.transfer_url,
            {
                "amount": "10.00",
                "to_account_number": self.alice_account.account_number,
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("to_account_number", r.data)

    def test_transfer_insufficient_funds(self):
        over = WELCOME_CREDIT_AMOUNT + Decimal("0.01")
        r = self.client.post(
            self.transfer_url,
            {"amount": str(over), "to_account_number": self.bob_number},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", r.data)

    def test_transfer_rejects_when_fee_consumes_almost_all(self):
        # Fee 5.00 on gross 5.00 leaves 0 for recipient (< 0.01 minimum credit).
        r = self.client.post(
            self.transfer_url,
            {"amount": "5.00", "to_account_number": self.bob_number},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", r.data)

    def test_parallel_transfers_one_fails_when_overdrawn(self):
        """Two concurrent gross debits that exceed balance together: only one may succeed."""
        token = str(RefreshToken.for_user(self.alice).access_token)
        barrier = threading.Barrier(2)
        statuses: list[int] = []

        def post_transfer():
            close_old_connections()
            try:
                c = APIClient()
                c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
                barrier.wait()
                r = c.post(
                    self.transfer_url,
                    {"amount": "6000.00", "to_account_number": self.bob_number},
                    format="json",
                )
                statuses.append(r.status_code)
            finally:
                close_old_connections()

        t1 = threading.Thread(target=post_transfer)
        t2 = threading.Thread(target=post_transfer)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(statuses), 2)
        self.assertEqual(sorted(statuses), [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        self.alice_account.refresh_from_db()
        self.assertGreaterEqual(self.alice_account.balance, Decimal("0"))
