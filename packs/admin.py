from django.contrib import admin
from .models import Pack

@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ("name", "usd_value", "daily_missions", "daily_withdrawals", "profit_percentage", "special_product_percentage", "is_active",'short_description','description', "created_by", "created_at")
    list_filter = ("is_active", "created_by")
    search_fields = ("name",)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'usd_value', 'icon', 'is_active')
        }),
        ('Mission Settings', {
            'fields': ('daily_missions', 'daily_withdrawals', 'number_of_set')
        }),
        ('Profit Settings', {
            'fields': ('profit_percentage', 'special_product_percentage')
        }),
        ('Bonus Settings', {
            'fields': ('payment_bonus', 'payment_limit_to_trigger_bonus')
        }),
        ('Other Settings', {
            'fields': ('minimum_balance_for_submissions', 'short_description', 'description', 'created_by')
        }),
    )
