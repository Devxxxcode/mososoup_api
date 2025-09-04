from notification.models import AdminLog
from django.contrib.auth.models import AnonymousUser

def create_admin_log(request, message, reason=None, actor=None):
    """
    Creates a log entry in the AdminLog model.
    
    Args:
        request (HttpRequest): The HTTP request object containing the user.
        message (str): The message to be logged.
        reason (str, optional): The reason for the log entry. Defaults to None.
    """
    try:
        # Prefer explicit actor when provided (e.g., admin login before request.user is authenticated)
        user = actor if actor is not None else getattr(request, "user", None)
        if user and not isinstance(user, AnonymousUser):
            AdminLog.objects.create(
                user=user,
                description=message,
                reason=reason
            )
            print("Admin log created successfully.")
        else:
            # Create a system log without user context
            AdminLog.objects.create(
                user=None,
                description=message,
                reason=reason
            )
            print("System admin log created (no authenticated user).")
    except Exception as e:
        # Optional: Use a logger here for better production error handling.
        print(f"Failed to create admin log: {str(e)}")
