from django.contrib.auth import get_user_model
from django.db import models

# User = get_user_model()

class Notification(models.Model):
    # Choices for notification types
    USER = 'user'
    ADMIN = 'admin'
    TYPE_CHOICES = [
        (USER, 'User'),
        (ADMIN, 'Admin'),
    ]

    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="notifications",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=USER)  # Type field

    def __str__(self):
        return f"Notification for {self.user.username if self.user else 'admin'}: {self.title}"

    class Meta:
        ordering = ['is_read', '-created_at']

    @classmethod
    def mark_all_user_as_read(cls, user):
        """
        Mark all notifications for a user as read.
        """
        cls.objects.filter(user=user, is_read=False,type=cls.USER).update(is_read=True)

    @classmethod
    def mark_all_admin_as_read(cls):
        """
        Mark all notifications for a user as read.
        """
        cls.objects.filter(is_read=False,type=cls.ADMIN).update(is_read=True)

    def mark_as_read(self):
        """
        Mark a single notification as read.
        """
        if not self.is_read:
            self.is_read = True
            self.save()


class AdminLog(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="admin_logs",
        null=True,
        blank=True,
    )
    description = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(null=True,blank=True)

    class Meta:
        ordering = ['-created_at']

    