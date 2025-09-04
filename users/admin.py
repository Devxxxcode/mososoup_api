from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
from wallet.models import Wallet

class WalletInline(admin.StackedInline):
    """
    Inline admin for Wallet details.
    """
    model = Wallet
    can_delete = False
    verbose_name_plural = "Wallet"
    # readonly_fields = ("balance", "on_hold")  # Example fields to make readonly

class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the custom User model.
    """

    # Fields to display in the list view
    list_display = ("username", "email", "phone_number", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "gender")

    # Fieldsets for the detail view
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (_("Personal Info"), {"fields": ("first_name", "last_name", "phone_number", "gender", "transactional_password",)}),
        (_("Permissions"), {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions","is_min_balance_for_submission_removed","is_reg_balance_add")}),
        (_("Important Dates"), {"fields": ("last_login", "date_joined","last_connection")}),
        (_("Submission Details"), {"fields": ("number_of_submission_today", "today_profit", "number_of_submission_set_today")}),
    )

    # Make `date_joined` readonly
    readonly_fields = ("date_joined",'referral_code')

    # Fields for the add view
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "first_name", "last_name", "phone_number", "gender"),
        }),
    )

    # Fields to search
    search_fields = ("username", "email", "phone_number")

    # Default ordering
    ordering = ("date_joined",)

    # Fields to use for editing
    filter_horizontal = ("groups", "user_permissions")

    # Inline wallet details
    inlines = [WalletInline]

# Register the custom User model and its admin
admin.site.register(User, UserAdmin)
