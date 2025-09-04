import random
from .models import OnHoldPay

def create_on_hold_pay_instances(start=1000, end=50000, min_diff=500, max_diff=5000):
    """
    Create OnHoldPay instances with random differences between min_amount and max_amount.
    
    Args:
        start (int): Starting value for the min_amount.
        end (int): Upper limit for the max_amount.
        min_diff (int): Minimum difference between min_amount and max_amount.
        max_diff (int): Maximum difference between min_amount and max_amount.
    """
    current_min = start

    while current_min < end:
        # Generate a random difference
        difference = random.randint(min_diff, max_diff)
        # Calculate the max amount
        current_max = min(current_min + difference, end)

        # Create the instance
        OnHoldPay.objects.create(
            min_amount=current_min,
            max_amount=current_max,
            is_active=True
        )

        # Move to the next range
        current_min = current_max + 1

    print(f"Instances created from {start} to {end}.")

# Call the function
create_on_hold_pay_instances()
