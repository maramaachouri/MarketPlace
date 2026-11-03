
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "MarketPlace",
            {"fields": ("role", "seller_status")},
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "MarketPlace",
            {"fields": ("role", "seller_status")},
        ),
    )

    list_display = (
        "username",
        "email",
        "role",
        "seller_status",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "seller_status",
        "is_staff",
        "is_active",
    )

    search_fields = ("username", "email", "first_name", "last_name")

    actions = ["approve_sellers", "reject_sellers"]

    @admin.action(description="Approuver les vendeurs sélectionnés")
    def approve_sellers(self, request, queryset):
        updated = queryset.filter(
            role=User.Role.SELLER
        ).update(seller_status=User.SellerStatus.APPROVED)

        self.message_user(
            request,
            f"{updated} vendeur(s) approuvé(s).",
        )

    @admin.action(description="Refuser les vendeurs sélectionnés")
    def reject_sellers(self, request, queryset):
        updated = queryset.filter(
            role=User.Role.SELLER
        ).update(seller_status=User.SellerStatus.REJECTED)

        self.message_user(
            request,
            f"{updated} vendeur(s) refusé(s).",
        )
