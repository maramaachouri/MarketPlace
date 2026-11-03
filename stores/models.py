
from django.conf import settings
from django.db import models


class Store(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        APPROVED = "APPROVED", "Approuvée"
        REJECTED = "REJECTED", "Refusée"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="store",
        limit_choices_to={"role": "SELLER"},
    )

    name = models.CharField(max_length=150)
    description = models.TextField()
    logo = models.ImageField(
        upload_to="stores/logos/",
        blank=True,
        null=True,
    )
    address = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
