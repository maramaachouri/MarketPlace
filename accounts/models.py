
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        SELLER = "SELLER", "Vendeur"
        ADMIN = "ADMIN", "Administrateur"

    class SellerStatus(models.TextChoices):
        PENDING = "PENDING", "En attente"
        APPROVED = "APPROVED", "Approuvé"
        REJECTED = "REJECTED", "Refusé"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    seller_status = models.CharField(
        max_length=10,
        choices=SellerStatus.choices,
        default=SellerStatus.PENDING,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
