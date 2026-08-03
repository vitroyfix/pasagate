from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Dashboard login account. A user OWNS one or more merchants —
    most will own exactly one, but this allows an agency/dev managing
    several merchant accounts under a single login.
    """
    ROLE_OWNER = "owner"
    ROLE_STAFF = "staff"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_STAFF, "Staff"),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_OWNER)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username