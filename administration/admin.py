from django.contrib import admin
from django.utils.html import format_html
from .models import Settings,Event,DailyResetTracker

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for managing global settings.
    """
    list_display = [
        "percentage_of_sponsors",
        "bonus_when_registering",
        "service_availability_start_time",
        "service_availability_end_time",
        "token_validity_period_hours",
        "timezone",
        "video_preview",  # Add video preview to the list view
    ]
    readonly_fields = ["video_preview"]  # Preview video in the admin detail view

    fieldsets = (
        ("General", {
            "fields": (
                "percentage_of_sponsors",
                "bonus_when_registering",
                "minimum_balance_for_submissions",
                "token_validity_period_hours",
            ),
        }),
        ("Service Availability", {
            "fields": (
                "service_availability_start_time",
                "service_availability_end_time",
                "timezone",
            ),
        }),
        ("Contacts", {
            "fields": (
                "whatsapp_contact",
                "telegram_contact",
                "telegram_username",
                "online_chat_url",
            ),
        }),
        ("Blockchain Addresses", {
            "fields": (
                "erc_address",
                "trc_address",
            ),
        }),
        ("Video Management", {  # New section for video management
            "fields": (
                "video",
                "video_preview",  # Add a preview field for the video
            ),
        }),
    )

    def video_preview(self, obj):
        """
        Render an HTML video player to preview the uploaded video.
        """
        if obj.video:
            return format_html(
                f'<video width="320" height="240" controls>'
                f'<source src="{obj.video.url}" type="video/mp4">'
                f'Your browser does not support the video tag.'
                f'</video>'
            )
        return "No video uploaded"

    video_preview.short_description = "Video Preview"

    def has_add_permission(self, request):
        # Limit to a single instance
        return not Settings.objects.exists()

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Event model.
    """
    list_display = ('name', 'is_active', 'created_at', 'created_by','image_preview')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'image', 'is_active')
        }),
        ('Additional Info', {
            'fields': ('created_at', 'created_by'),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Image"


@admin.register(DailyResetTracker)
class DailyResetTrackerAdmin(admin.ModelAdmin):
    """
    Admin interface for the DailyResetTracker model.
    """
    list_display = ('last_reset_time', 'reset_interval_hours') 
    list_editable = ('reset_interval_hours',) 
    readonly_fields = ('last_reset_time',)
    ordering = ('-last_reset_time',) 
    search_fields = ('last_reset_time',)