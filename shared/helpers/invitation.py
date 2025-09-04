import random
import string

def generate_invitation_code():
    """
    Generate a random 6-character alphanumeric invitation code.
    """
    return ''.join(random.choices(string.ascii_uppercase, k=6))