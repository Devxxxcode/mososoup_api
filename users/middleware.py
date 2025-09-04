from datetime import datetime
from django.utils.timezone import now
from django.utils.timezone import now, timedelta
from administration.models import DailyResetTracker
from django.contrib.auth import get_user_model
from django.utils.timezone import now
import pytz
import random

User = get_user_model()


class UpdateLastConnectionMiddleware:
    """
    Middleware to update the `last_connection` field for authenticated users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update last_connection only for authenticated users
        if request.user.is_authenticated:
            request.user.last_connection = now()
            request.user.save(update_fields=['last_connection'])

        response = self.get_response(request)
        return response
    
import time

class SlowDownMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        wait_time = random.randint(2, 4)
        print(f"Waiting for {wait_time} seconds...")
        time.sleep(wait_time)
        print(f"Wait completed")
        response = self.get_response(request)
        return response

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.timezone import now

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        user_and_token = super().authenticate(request)
        if not user_and_token:
            return user_and_token

        user, validated_token = user_and_token

        # Enforce per-session UUID claim (sid) per surface indicated by token claim
        payload = validated_token.payload
        
        sid = payload.get("sid")
        surf = payload.get("surf", "user")
        current_sid = str(getattr(user, "session_uuid_admin" if surf == "admin" else "session_uuid_user", ""))
        if not sid or sid != current_sid:
            raise AuthenticationFailed("Session has been invalidated. Please log in again.")

        if not user.is_staff:
            user.last_connection = now()
            user.save(update_fields=['last_connection'])
        return (user, validated_token)


class ConfigurableResetMiddleware:
    """
    Middleware to reset user submission-related fields based on a configurable time interval.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ensure the reset action is performed
        self.check_and_reset_fields()

        # Proceed with the response
        response = self.get_response(request)
        return response

    # def check_and_reset_fields(self):
    #     """
    #     Check the last reset time and reset fields if the interval has passed.
    #     """
    #     # Get or create the tracker entry
    #     tracker, created = DailyResetTracker.objects.get_or_create(id=1)  # Use a fixed ID for simplicity

    #     # Calculate the reset interval in hours
    #     reset_interval = timedelta(hours=float(tracker.reset_interval_hours))  # Convert to float

    #     # Perform reset if the interval has passed
    #     if now() >= tracker.last_reset_time + reset_interval:
    #         self.perform_reset()
    #         # Update the last reset time
    #         tracker.last_reset_time = now()
    #         tracker.save()


    def check_and_reset_fields(self):
        # Define Eastern Time timezone
        eastern_time = pytz.timezone("US/Eastern")

        # Get or create tracker entry
        tracker, created = DailyResetTracker.objects.get_or_create(id=1)

        # Calculate today's 12:00 AM in Eastern Time
        today_midnight = now().astimezone(eastern_time).replace(hour=0, minute=0, second=0, microsecond=0)

        # Convert today's midnight to UTC
        today_midnight_utc = today_midnight.astimezone(pytz.UTC)

        # Perform reset if last reset time is earlier than today's midnight
        if tracker.last_reset_time < today_midnight_utc:
            self.perform_reset()
            # Update the last reset time to today's midnight in UTC
            tracker.last_reset_time = today_midnight_utc
            tracker.save()


    def perform_reset(self):
        """
        Reset user fields to their default values.
        """
        try:
            users_with_pending_games = User.objects.filter(
                games__played=False, games__pending=True, games__is_active=True, games__special_product=True
            ).distinct()

            # Reset wallet salary for users with pending games
            users_with_pending_games.update(
                number_of_submission_set_today=0
            )
            for user in users_with_pending_games:
                if hasattr(user, "wallet"):
                    user.wallet.salary = 0
                    user.wallet.save()

            # Reset other users' fields in bulk
            other_users = User.objects.exclude(id__in=users_with_pending_games)
            other_users.update(
                number_of_submission_today=0,
                today_profit=0.00,
                number_of_submission_set_today=0
            )
            for user in other_users:
                if hasattr(user, "wallet"):
                    user.wallet.salary = 0
                    user.wallet.save()

            print("User fields reset successfully.")
        except Exception as e:
            print(f"Error in perform_reset: {e}")

