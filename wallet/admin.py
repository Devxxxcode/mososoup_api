from django.contrib import admin
from .models import OnHoldPay

@admin.register(OnHoldPay)
class OnHoldPayAdmin(admin.ModelAdmin):
    """
    Admin configuration for the OnHoldPay model.
    """
    list_display = ('min_amount', 'max_amount', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('min_amount', 'max_amount')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('min_amount', 'max_amount', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
