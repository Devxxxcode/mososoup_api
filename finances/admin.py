from django.contrib import admin
from .models import Deposit,Withdrawal,PaymentMethod

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "date_time", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "amount")


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("user", "payment_method", "amount", "status", "transaction_reference", "created_at")
    list_filter = ("status", "payment_method__name")
    search_fields = ("user__username", "transaction_reference", "payment_method__name")

    readonly_fields = ("transaction_reference",)  # Display the field as read-only in the admin detail view

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "phone_number", "email_address", "wallet", "exchange", "is_active")
    list_filter = ("is_active", "name")
    search_fields = ("user__username", "name", "email_address", "phone_number")