from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterResponseSerializer, RegisterSerializer
from .services import register_user_with_account


@extend_schema(
    tags=["auth"],
    request=RegisterSerializer,
    responses={201: RegisterResponseSerializer},
    summary="Register",
    description="Create user, bank account, and apply welcome credit in one transaction.",
    auth=[],
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        _user, account = register_user_with_account(email=email, password=password)
        return Response(
            {
                "email": email,
                "account_number": account.account_number,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["auth"],
    request=TokenObtainPairSerializer,
    summary="Login (JWT)",
    description="Obtain access and refresh tokens. Send `email` and `password`.",
    auth=[],
)
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
