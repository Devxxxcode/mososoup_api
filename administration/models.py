from django.db import models
from cloudinary_storage.storage import MediaCloudinaryStorage
from cloudinary.models import CloudinaryField
import cloudinary
from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model

# User = get_user_model()

class Settings(models.Model):
    """
    Model to store global settings for the application.
    """
    percentage_of_sponsors = models.PositiveIntegerField(default=0, verbose_name="Percentage of Sponsors")
    bonus_when_registering = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Bonus When Registering (USD)")
    service_availability_start_time = models.TimeField(verbose_name="Service Availability Start Time")
    service_availability_end_time = models.TimeField(verbose_name="Service Availability End Time")
    token_validity_period_hours = models.PositiveIntegerField(default=0, verbose_name="Token Validity Period (Hours)")
    whatsapp_contact = models.CharField(max_length=100, blank=True, null=True, verbose_name="WhatsApp Contact")
    telegram_contact = models.CharField(max_length=100, blank=True, null=True, verbose_name="Telegram Contact")
    telegram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Telegram Username")
    online_chat_url = models.URLField(blank=True, null=True, verbose_name="Online Chat URL")
    online_embed_url =  models.URLField(blank=True, null=True, verbose_name="Online Embed URL")
    erc_address = models.CharField(max_length=100, blank=True, null=True, verbose_name="ERC Address")
    trc_address = models.CharField(max_length=100, blank=True, null=True, verbose_name="TRC Address")
    minimum_balance_for_submissions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Minimum Balance for Submissions")
    video = CloudinaryField(
        "video", 
        resource_type="video",
        folder="videos/", 
        blank=True,
        null=True
    )
    timezone = models.CharField(max_length=50, default="UTC", verbose_name="Time Zone")

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"

    def __str__(self):
        return "Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and Settings.objects.exists():
            raise ValueError("There can only be one instance of Settings.")
        super(Settings, self).save(*args, **kwargs)

class Event(models.Model):
    name = models.CharField(max_length=255, verbose_name="Event Name")
    description = models.TextField(verbose_name="Event Description")
    image =models.ImageField(upload_to='events/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    created_by = models.ForeignKey(
    "users.User",
    on_delete=models.SET_NULL, 
    related_name="events_created",  # For reverse relation naming
    null=True,  # Allow NULL values
    blank=True,  # Optional: Allow blank in forms (useful for admin or forms)
    verbose_name="Created By"
)

    def __str__(self):
        return f"Event named {self.name}"
    
    class Meta:
        ordering = ['-created_at']


def midnight_today():
    """
    Returns 12:00 AM of the current day in the current timezone.
    """
    current_time = now()
    midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight


class DailyResetTracker(models.Model):
    last_reset_time = models.DateTimeField(default=midnight_today, verbose_name="Last Reset Time")
    reset_interval_hours = models.DecimalField(
        max_digits=5,  # Maximum number of digits, including decimals
        decimal_places=2,  # Number of decimal places
        default=24.00,  # Default to 24 hours
        verbose_name="Reset Interval in Hours",
    )