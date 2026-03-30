from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Bank user identified by email (no username)."""

    username = None
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email
