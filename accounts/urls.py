from django.urls import path

from .views import BalanceView, TransactionListView

urlpatterns = [
    path("accounts/balance/", BalanceView.as_view(), name="account-balance"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
]
