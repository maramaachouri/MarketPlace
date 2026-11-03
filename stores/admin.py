
from django.contrib import admin
from django.utils import timezone

from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("name", "owner__username", "owner__email")
    readonly_fields = ("created_at", "updated_at")

    actions = ["approve_stores", "reject_stores"]

    @admin.action(description="Approuver les boutiques sélectionnées")
    def approve_stores(self, request, queryset):
        updated = queryset.update(status=Store.Status.APPROVED)
        self.message_user(
            request,
            f"{updated} boutique(s) approuvée(s)."
        )

    @admin.action(description="Refuser les boutiques sélectionnées")
    def reject_stores(self, request, queryset):
        updated = queryset.update(status=Store.Status.REJECTED)
        self.message_user(
            request,
            f"{updated} boutique(s) refusée(s)."
        )
