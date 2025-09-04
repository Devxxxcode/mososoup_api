import random
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
# from wallet.models import OnHoldPay
from django.core.validators import MinValueValidator

User = get_user_model()


def generate_unique_rating_no():
    """
    Generate a unique 11-digit number for rating_no.
    """
    while True:
        rating_no = ''.join([str(random.randint(0, 9)) for _ in range(11)])
        if not Product.objects.filter(rating_no=rating_no).exists():
            return rating_no


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/')
    rating_no = models.CharField(max_length=11, unique=True, editable=False, blank=True)  # Unique 11-digit number
    date_created = models.DateTimeField(auto_now_add=True)  # Corrected typo from `auto_add_now`

    def save(self, *args, **kwargs):
        # Generate unique rating_no if not already set
        if not self.rating_no:
            self.rating_no = generate_unique_rating_no()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Game(models.Model):
    products = models.ManyToManyField('Product', related_name="games")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="games")  
    rating_score = models.PositiveIntegerField(blank=True,null=True)  
    comment = models.TextField(max_length=500, blank=True,null=True) 
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True) 
    played = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Commission Percentage Used")
    special_product = models.BooleanField(default=False)
    game_number = models.IntegerField(null=True,blank=True)
    pending = models.BooleanField(default=False)
    rating_no = models.CharField(max_length=11,blank=True)  # Unique 11-digit number
    is_active = models.BooleanField(default=True)
    on_hold = models.ForeignKey(
        "wallet.OnHoldPay", 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="negative_games",
        help_text="Reference to the on-hold payment associated with this game."
        )
    
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        """
        Override save method to enforce a maximum of 3 products per game.
        """
        super().save(*args, **kwargs)
        if not self.rating_no:
            self.rating_no = generate_unique_rating_no()
        if self.products.count() > 3:
            raise ValueError("A game cannot have more than 3 products.")

    @classmethod
    def count_games_played_today(cls, user):
        """
        Count the number of games a user has played today.
        """
        # Calculate the start and end of the current day
        # start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
        # end_of_day = start_of_day + timedelta(days=1)

        # # Count games played by the user today
        # return cls.objects.filter(
        #     user=user,
        #     played=True,  # Ensure we only count played games
        #     is_active=True,
        #     created_at__gte=start_of_day,
        #     created_at__lt=end_of_day
        # ).count()
        return user.number_of_submission_today
    
    @classmethod
    def user_has_pending_game(cls,user):
        '''
        check if the user has pending game play 
        '''
        return cls.objects.filter(user=user, played=False,pending=True,is_active=True).exists()

    def __str__(self):
        names = list(self.products.values_list("name", flat=True)[:3])
        label = ", ".join(names) if names else "no products"
        return f"Game [{label}] by {self.user.username}"


# class NegativeUser(models.Model):
#     user = models.OneToOneField(
#         User, 
#         on_delete=models.CASCADE, 
#         related_name="negative_user",
#         help_text="The user associated with negative reviews or activity."
#     )
#     on_hold = models.ForeignKey(
#         "wallet.OnHoldPay", 
#         on_delete=models.CASCADE, 
#         related_name="negative_users",
#         help_text="Reference to the on-hold payment associated with this user."
#     )
#     number_of_negative_product = models.IntegerField(
#         validators=[
#             MinValueValidator(0)
#         ],
#         help_text="Number of negative products associated with the user."
#     )
#     rank_appearance = models.IntegerField(
#         validators=[
#             MinValueValidator(0)
#         ],
#         help_text="The ranks number for the product to show."
#     )

#     def __str__(self):
#         return f"NegativeUser: {self.user.username} - Negative Products: {self.number_of_negative_product}"

