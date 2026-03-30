from django.urls import path

from .views import AccountNumberView, BalanceView, TransactionListView, TransferView

urlpatterns = [
    path(
        "accounts/account-number/",
        AccountNumberView.as_view(),
        name="account-number",
    ),
    path("accounts/balance/", BalanceView.as_view(), name="account-balance"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("transfers/", TransferView.as_view(), name="transfer-create"),
]
