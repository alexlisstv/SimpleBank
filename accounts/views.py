from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account, Transaction
from .pagination import TransactionPagination
from .serializers import BalanceSerializer, TransactionListSerializer
from .time_bounds import transaction_time_bounds


def _account_for_user(user) -> Account:
    try:
        return user.account
    except Account.DoesNotExist as exc:
        raise NotFound("No bank account for this user.") from exc


@extend_schema(
    tags=["accounts"],
    summary="Account balance",
    description="Current user's account balance as a decimal string (no precision loss).",
    responses={200: BalanceSerializer},
)
class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        account = _account_for_user(request.user)
        return Response(BalanceSerializer(account).data)


@extend_schema(
    tags=["transactions"],
    summary="Transaction history",
    description="List ledger rows for the current user's account. Optional UTC date/datetime bounds `from` and `to` (inclusive).",
    parameters=[
        OpenApiParameter(
            name="from",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Lower bound (ISO date or datetime, UTC).",
        ),
        OpenApiParameter(
            name="to",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Upper bound (ISO date or datetime, UTC). Date-only values include end of that UTC day.",
        ),
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="page_size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
    ],
)
class TransactionListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionListSerializer
    pagination_class = TransactionPagination

    def get_queryset(self):
        start, end = transaction_time_bounds(self.request.query_params)
        account = _account_for_user(self.request.user)
        qs = Transaction.objects.filter(account=account).order_by("-timestamp", "-pk")
        if start is not None:
            qs = qs.filter(timestamp__gte=start)
        if end is not None:
            qs = qs.filter(timestamp__lte=end)
        return qs
