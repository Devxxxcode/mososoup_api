from typing import Optional
from notification.models import Notification

def create_user_notification(user: "User", title: Optional[str] = None, message: str = "", type: str = Notification.USER) -> Notification:
    """
    Helper function to create a notification for a user.

    Args:
        user (User): The user to whom the notification belongs.
        title (Optional[str]): The title of the notification. Defaults to None.
        message (str): The message body of the notification.
        type (str): The type of the notification. Must be one of Notification.TYPE_CHOICES.

    Returns:
        Notification: The created notification instance.
    
    Raises:
        ValueError: If the user or message is not provided, or if type is invalid.
    """
    if not user:
        raise ValueError("User must be provided to create a notification.")
    if not message:
        raise ValueError("Message must be provided to create a notification.")
    if type not in dict(Notification.TYPE_CHOICES).keys():
        raise ValueError(f"Invalid notification type. Allowed types: {', '.join(dict(Notification.TYPE_CHOICES).keys())}")
    
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type
    )
    return notification


def create_admin_notification(title: Optional[str] = None, message: str = "", type: str = Notification.ADMIN) -> Notification:
    """
    Helper function to create a notification for an admin user.

    Args:
        title (Optional[str]): The title of the notification. Defaults to None.
        message (str): The message body of the notification.
        type (str): The type of the notification. Must be one of Notification.TYPE_CHOICES.

    Returns:
        Notification: The created notification instance.
    
    Raises:
        ValueError: If the admin or message is not provided, or if type is invalid.
    """
    if not message:
        raise ValueError("Message must be provided to create a notification.")
    if type not in dict(Notification.TYPE_CHOICES).keys():
        raise ValueError(f"Invalid notification type. Allowed types: {', '.join(dict(Notification.TYPE_CHOICES).keys())}")

    notification = Notification.objects.create(
        user=None,
        title=title,
        message=message,
        type=type
    )
    return notification
