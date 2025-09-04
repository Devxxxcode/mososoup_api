from django.contrib import admin
from .models import Product,Game

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'rating_no', 'date_created')
    search_fields = ('name', 'description')
    list_filter = ('date_created',)
    readonly_fields = ('rating_no', 'date_created')
    ordering = ('-date_created',)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'rating_score', 'played', 'pending', 'special_product', 'created_at', 'updated_at')
    search_fields = ('user__username', 'rating_no')
    list_filter = ('played', 'special_product', 'pending', 'created_at')
    readonly_fields = ('rating_no', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    filter_horizontal = ('products',)  # To manage many-to-many relationships in the admin UI

    def save_model(self, request, obj, form, change):
        # Custom save logic (if needed)
        if obj.products.count() > 3:
            raise ValueError("A game cannot have more than 3 products.")
        super().save_model(request, obj, form, change)
