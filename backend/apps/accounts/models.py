from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Single-role user. Email is the login identifier."""

    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
