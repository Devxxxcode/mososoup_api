from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()  


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows authentication using email or username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Look up user by username or email
            user = User.objects.get(
                Q(username=username) | Q(email__iexact=username)
            )
            # Validate the password
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        """
        Retrieve the user by their ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
