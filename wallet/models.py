from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from packs.models import Pack
from game.models import Game

User = get_user_model()


class Wallet(models.Model):
    """
    Wallet model to manage user's financial details.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE, 
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Wallet Balance"
    )
    on_hold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Amount On Hold"
    )
    commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Commission Earned"
    )
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Salary Earned"
    )
    credit_score = models.DecimalField(
        max_digits=5,  # Adjusted for scores between 0.00 and 100.00
        decimal_places=2,
        default=100.00,  # Changed from 0.00 to 100.00
        verbose_name="Credit Score",
        validators=[
            MinValueValidator(0.00),
            MaxValueValidator(100.00)
        ]
    )
    package = models.ForeignKey(
        Pack, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="wallet_pack"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.username} - Balance: {self.balance}"

    def credit(self, amount):
        """
        Add funds to the wallet balance and handle negative balance clearing.
        Since on_hold and balance can never both be positive, we handle them sequentially.
        """
        # First: Clear negative balance if exists
        if self.balance < 0:
            if amount >= abs(self.balance):
                # Clear entire negative balance and add remaining to balance
                remaining_amount = amount - abs(self.balance)
                self.balance = remaining_amount
            else:
                # Partial clear of negative balance
                self.balance += amount
        else:
            # Normal deposit - add amount to balance
            self.balance += amount
        
        # If balance is now non-negative and on_hold exists, move on_hold to balance
        # This ensures on_hold and balance are never both positive
        if self.balance >= 0 and self.on_hold > 0:
            self.balance += self.on_hold
            self.on_hold = 0
        
        self.save()

    def credit_commission(self, amount):
        """
        Add funds to the Commission balance.
        """
        if amount < 0:
            raise ValueError("Credit amount must be positive.")
        
        self.commission += amount
        self.save()

    def debit_commission(self, amount):
        """
        Add funds to the Commission balance.
        """
        if amount < 0:
            raise ValueError("Credit amount must be positive.")
        
        self.commission -= amount
        self.save()

    def debit(self, amount):
        """
        Deduct funds from the wallet balance. Now works with negative balance.
        """
        if amount < 0:
            raise ValueError("Debit amount must be positive.")
        
        if self.balance >= amount:
            self.balance -= amount
        else:
            # Store initial balance before making it negative
            initial_balance = self.balance
            # Calculate how much more is needed
            deficit = amount - self.balance
            # Set balance to negative (shows deficit)
            self.balance = -deficit
            # Set on_hold to just the game amount (what needs to be reserved)
            self.on_hold = amount
        
        self.save()


    def add_on_hold(self, amount):
        """
        Add funds to the 'on_hold' balance.
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        self.on_hold += amount
        self.save()

    def release_on_hold(self, amount):
        """
        Release funds from 'on_hold' to 'balance'.
        """
        if amount <= 0 or self.on_hold < amount:
            raise ValueError("Invalid release amount.")
        self.on_hold -= amount
        self.balance += amount
        self.save()

    def save(self, *args, **kwargs):
        """
        Assign a Pack based on the wallet balance ONLY on creation or when no pack is set.
        """
        is_new = self._state.adding
        if is_new or not self.package or (self.package and not self.package.is_active):
            # Fetch all active packs ordered by their USD value in descending order
            packs = Pack.objects.filter(is_active=True).order_by('-usd_value')

            # Attempt to assign the highest suitable pack
            assigned_pack = None
            for pack in packs:
                if self.balance >= pack.usd_value:
                    assigned_pack = pack
                    break

            # Fall back to the pack with the lowest value if no suitable pack was found
            if not assigned_pack:
                assigned_pack = Pack.objects.filter(is_active=True).order_by('usd_value').first()

            # Assign the selected pack to the instance
            self.package = assigned_pack

        # Call the parent save method
        super().save(*args, **kwargs)


        
class OnHoldPay(models.Model):
    min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="min amount for the on hold range"
    )
    max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="max amount for the on hold range"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Range from {self.min_amount} - {self.max_amount}"