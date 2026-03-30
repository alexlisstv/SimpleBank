from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from urllib.parse import urlencode

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.constants import WELCOME_CREDIT_AMOUNT
from accounts.models import Account, Transaction
from users.models import User


def _auth_client(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")


class BalanceAndTransactionsAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse("auth-register")
        self.password = "Str0ng!pass_for_tests"
        reg = self.client.post(
            self.register_url,
            {"email": "owner@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)
        self.user = User.objects.get(email="owner@example.com")
        self.account = Account.objects.get(user=self.user)
        _auth_client(self.client, self.user)
        self.balance_url = reverse("account-balance")
        self.transactions_url = reverse("transaction-list")

    def test_balance_requires_auth(self):
        self.client.credentials()
        r = self.client.get(self.balance_url)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_balance_returns_string_decimal(self):
        r = self.client.get(self.balance_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data, {"balance": str(WELCOME_CREDIT_AMOUNT)})
        self.assertIsInstance(r.data["balance"], str)

    def test_transactions_lists_welcome_credit(self):
        r = self.client.get(self.transactions_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("results", r.data)
        self.assertEqual(len(r.data["results"]), 1)
        row = r.data["results"][0]
        self.assertEqual(row["amount"], str(WELCOME_CREDIT_AMOUNT))
        self.assertEqual(row["type"], Transaction.Type.CREDIT)
        self.assertIn("timestamp", row)

    def test_transactions_date_filter_inclusive(self):
        tx = Transaction.objects.create(
            account=self.account,
            amount=Decimal("1.00"),
            type=Transaction.Type.DEBIT,
        )
        mid = datetime(2024, 6, 15, 12, 0, 0, tzinfo=dt_timezone.utc)
        Transaction.objects.filter(pk=tx.pk).update(timestamp=mid)

        qs = urlencode({"from": "2024-06-15", "to": "2024-06-15"})
        r = self.client.get(f"{self.transactions_url}?{qs}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        amounts = [row["amount"] for row in r.data["results"]]
        self.assertEqual(amounts, ["1.00"])

    def test_transactions_rejects_from_after_to(self):
        r = self.client.get(
            self.transactions_url,
            {"from": "2024-06-20", "to": "2024-06-10"},
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transactions_rejects_invalid_from(self):
        r = self.client.get(self.transactions_url, {"from": "not-a-date"})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("from", r.data)
