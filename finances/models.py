from django.db import models
from django.db.models import Sum
from django.contrib.auth import get_user_model
import uuid
from game.models import Game
from django.utils.timezone import now, timedelta
User = get_user_model()

class Deposit(models.Model):
    """
    Model to represent deposits made by users.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='deposits', verbose_name="User"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Amount"
    )
    date_time = models.DateTimeField(auto_now_add=True, verbose_name="Date and Time")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="Status"
    )
    screenshot = models.ImageField(
        upload_to='deposit_screenshots/', null=False, blank=False, verbose_name="Screenshot"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Deposit by {self.user.username} - {self.amount} USD - {self.status}"

    class Meta:
        ordering = ['-created_at']



class PaymentMethod(models.Model):
    """
    Model to represent a user's payment method for withdrawals.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="payment_method",
        verbose_name="User"
    )
    name = models.CharField(
        max_length=50, verbose_name="Payment Method Name"
    )
    phone_number = models.CharField(
        max_length=20, verbose_name="Phone Number", blank=True, null=True
    )
    email_address = models.EmailField(
        max_length=254, verbose_name="Email Address", blank=True, null=True
    )
    wallet = models.CharField(
        max_length=200, verbose_name="Wallet Address", blank=True, null=True
    )
    exchange = models.CharField(
        max_length=100, verbose_name="Exchange Platform", blank=True, null=True
    )
    is_active = models.BooleanField(
        default=True, verbose_name="Is Active"
    )

    def __str__(self):
        return f"{self.name} ({self.user.username})"
    

class Withdrawal(models.Model):
    """
    Model to represent withdrawals made by users.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processed', 'Processed'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='withdrawals', verbose_name="User"
    )
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Payment Method"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Amount"
    )
    transaction_reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Transaction Reference",
        editable=False  # Make this field non-editable
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="Status"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_reviewed = models.BooleanField(default=False, verbose_name="Has the admin updated the status")

    def __str__(self):
        return f"Withdrawal by {self.user.username} - {self.amount} USD - {self.status}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """
        Auto-generate a unique transaction reference if not set.
        """
        if not self.transaction_reference:
            self.transaction_reference = str(uuid.uuid4()).replace('-', '').upper()[:12] 
        super(Withdrawal, self).save(*args, **kwargs)

    @classmethod
    def can_withdraw(cls,user,amount,transactional_password):
        """
        Check if the user can withdraw the specified amount.
        """
        wallet = user.wallet
        balance = wallet.balance
        pack = wallet.package
        number_of_play = Game.count_games_played_today(user)
        total_play = pack.daily_missions
        max_no_of_withdrawal = pack.daily_withdrawals
        if balance < amount:
            return False, f"Insufficient balance. Your balance is {balance}."
        if number_of_play < total_play:
            return False, (
                f"All {total_play} submission{'s' if total_play > 1 else ''} must be completed"
                f"before you are able to withdraw."
            )
        if number_of_play < pack.daily_missions:
            return False, (
                f"All {pack.daily_missions} mission{'s' if pack.daily_missions > 1 else ''} must be completed"
                f" before you are able to withdraw."
            )
        total_withdrawal_for_today = cls.total_count_of_today_withdrawal(user)
        # if total_withdrawal_for_today >= max_no_of_withdrawal:
        #     return False, f"You have reached the maximum number of withdrawal for today"
        if not user.check_transactional_password(transactional_password):
            return False, "Incorrect transactional password"

        # Prevent oversubscription: pending withdrawals reserve available balance
        pending_total = (
            cls.objects.filter(user=user, status='Pending', is_reviewed=False)
            .aggregate(total=Sum('amount'))
            .get('total') or 0
        )
        available = balance - pending_total
        if available <= 0:
            return False, (
                f"Insufficient available balance. You have pending withdrawals totaling {pending_total} USD."
            )
        if amount > available:
            return False, (
                f"Insufficient available balance. You can withdraw up to {available} USD."
            )
        return True,""

    
    @classmethod
    def total_count_of_today_withdrawal(cls,user):
        # Calculate the start and end of the current day
        start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Count games played by the user today
        return cls.objects.filter(
            user=user,
            created_at__gte=start_of_day,
            created_at__lt=end_of_day
        ).count()
