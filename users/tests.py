from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.constants import WELCOME_CREDIT_AMOUNT
from accounts.models import Account, Transaction
from users.models import User


class RegisterAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("auth-register")
        self.password = "Str0ng!pass_for_tests"

    def test_register_creates_user_account_and_welcome_credit(self):
        response = self.client.post(
            self.url,
            {"email": "new@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "new@example.com")
        self.assertRegex(response.data["account_number"], r"^\d{10}$")

        user = User.objects.get(email="new@example.com")
        account = Account.objects.get(user=user)
        self.assertEqual(account.account_number, response.data["account_number"])
        self.assertEqual(account.balance, WELCOME_CREDIT_AMOUNT)

        tx = Transaction.objects.get(account=account)
        self.assertEqual(tx.type, Transaction.Type.CREDIT)
        self.assertEqual(tx.amount, WELCOME_CREDIT_AMOUNT)

    def test_register_rejects_duplicate_email(self):
        payload = {"email": "dup@example.com", "password": self.password}
        r1 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        r2 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse("auth-register")
        self.login_url = reverse("auth-login")
        self.password = "Str0ng!pass_for_tests"
        self.client.post(
            self.register_url,
            {"email": "login@example.com", "password": self.password},
            format="json",
        )

    def test_login_returns_jwt_pair(self):
        response = self.client.post(
            self.login_url,
            {"email": "login@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
