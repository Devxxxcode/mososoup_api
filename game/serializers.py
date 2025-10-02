from rest_framework import serializers
from .models import Product,Game
from django.contrib.auth import get_user_model
from wallet.models import OnHoldPay
import random
from decimal import Decimal
from users.serializers import AdminUserUpdateSerializer
from itertools import combinations
from decimal import Decimal
from random import shuffle


User = get_user_model()

class OnHoldPaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OnHoldPay
        fields = "__all__"
        ref_name = "OnHoldPaySerializer game"


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model with custom validation.
    """

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'price',
            'image',
            'rating_no',
            'date_created',
        ]
        read_only_fields = ['rating_no', 'date_created']

    def validate_price(self, value):
        """
        Ensure the price is a positive number.
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value




class ProductList(serializers.ModelSerializer):
    """
    Serializer for listing products associated with a game.
    """
    class Meta:
        model = Product  # Fixed to reference the Product model
        fields = ['id', 'name', 'image', 'price', 'rating_no']


class GameSerializer:
    """
    Serializer container for games.
    """

    class PlayGameRequestSerializer(serializers.Serializer):
        """
        Serializer for the play game request payload.
        """
        rating_score = serializers.IntegerField(required=True)
        comment = serializers.CharField(required=False, allow_blank=True)

        def validate_rating_score(self, value):
            if not 1 <= value <= 5:
                raise serializers.ValidationError("Rating score must be between 1 and 5.")
            return value


    class Retrieve(serializers.ModelSerializer):
        """
        Serializer for retrieving game details, including products and limits.
        """
        total_number_can_play = serializers.SerializerMethodField()
        current_number_count = serializers.SerializerMethodField()
        products = ProductList(many=True)  # Correctly reference ProductList serializer

        class Meta:
            model = Game
            fields = [
                'id', 
                'products', 
                'amount', 
                'commission', 
                'commission_percentage',
                'total_number_can_play', 
                'current_number_count', 
                'rating_score',
                'comment',
                'special_product',
                'created_at',
                'rating_no',
                'game_number',
                'pending',
            ]
            ref_name = "Game Retrieve" 
            extra_kwargs = {
            'rating_score': {'write_only': True},
            'comment': {'write_only': True},
        }
        
        def get_total_number_can_play(self, obj):
            """
            Retrieve the total number of games the user can play.
            This should be passed in the serializer context.
            """
            return self.context.get('total_number_can_play', 0)

        def get_current_number_count(self, obj):
            """
            Retrieve the current number of games played by the user today.
            This should be passed in the serializer context.
            """
            return self.context.get('current_number_count', 0)
        
    class List(serializers.ModelSerializer):
        products = ProductList(many=True) 
        class Meta:
            model = Game
            fields = [
                'id', 
                'products', 
                'amount', 
                'commission', 
                'rating_score',
                'comment',
                'special_product',
                'updated_at',
                'rating_no',
                'pending',
            ]
            ref_name = "Game Retrieve" 


class AdminNegativeUserSerializer:

    class Create(serializers.ModelSerializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        on_hold = serializers.PrimaryKeyRelatedField(queryset=OnHoldPay.objects.filter(is_active=True),required=True)
        number_of_negative_product = serializers.IntegerField(required=True,min_value=0,max_value=3,help_text="Number of negative products must be between 0 and 3.")
        rank_appearance = serializers.IntegerField(required=True,min_value=0)
        
        class Meta:
            model = Game
            fields = ['user','on_hold','number_of_negative_product','rank_appearance']
            ref_name = "Negative User Create"

        
        def save(self):
            """Create or update a negative game for the user"""
            user = self.validated_data['user']
            
            # Get profit percentage from user's package
            try:
                profit_percentage = Decimal(user.wallet.package.profit_percentage)  # Ensure Decimal type
            except Exception as e:
                profit_percentage = Decimal('0.5')  # Default fallback
            
            on_hold = self.validated_data['on_hold']
            number_of_negative_product = self.validated_data.get(
                'number_of_negative_product', 
                self.instance.products.count() if self.instance else 0
            )
            rank_appearance = self.validated_data.get(
                'rank_appearance', 
                self.instance.game_number if self.instance else None
            )

            # Allow multiple special games for the same appearance (game_number)
            # The system will pick the first available one when the user reaches that appearance
            # products = Product.objects.order_by('?')[:number_of_negative_product]

            # Convert min and max to float for `random.uniform`
            on_hold_min = Decimal(on_hold.min_amount)  # Convert to Decimal
            on_hold_max = Decimal(on_hold.max_amount)  # Convert to Decimal
            balance = user.wallet.balance
            max_balance = balance + on_hold_max  # Now both are Decimal
            min_balance = balance + on_hold_min  # Now both are Decimal
            products_selected = self.select_products_within_range(min_balance,max_balance,number_of_negative_product)
            if len(products_selected) == 0:
                raise serializers.ValidationError({ "on_hold": f"No albums match the on-hold range ({on_hold_min} to {on_hold_max}) for the user balance with {balance}"})
            # Generate a random amount between min and max, then convert to Decimal
            random_amount = Decimal(random.uniform(float(on_hold_min), float(on_hold_max)))
            amount = balance + random_amount
            amount = amount.quantize(Decimal("0.01"))  # Ensure two decimal places

            # Calculate commission using special product percentage
            if user.wallet.package and user.wallet.package.special_product_percentage > 0:
                special_percentage = user.wallet.package.special_product_percentage
            else:
                special_percentage = profit_percentage * 5  # Fallback to 5x multiplier if no special percentage set
            
            commission = (amount * special_percentage / Decimal(100))
            commission = commission.quantize(Decimal("0.01"))  # Ensure two decimal place

            if self.instance:
                # Update existing instance
                self.instance.user = user
                self.instance.on_hold = on_hold
                self.instance.game_number = rank_appearance
                self.instance.amount = amount
                self.instance.commission = commission
                self.instance.commission_percentage = special_percentage
                self.instance.special_product = True
                self.instance.is_active = True
                self.instance.products.set(products_selected)
                self.instance.save()
                return self.instance
            else:
                # Create a new instance
                game = Game.objects.create(
                    user=user,
                    on_hold=on_hold,
                    game_number=rank_appearance,
                    played=False,
                    amount=amount,
                    commission=commission,
                    commission_percentage=special_percentage,
                    special_product=True,
                    is_active=True,
                )
                game.products.set(products_selected)
                return game
        
        
        def select_products_within_range(self, min_amount, max_amount, max_products):
            """
            Select a combination of products whose total price is within the specified range
            and whose number equals max_products.

            Args:
                min_amount (Decimal): Minimum total price.
                max_amount (Decimal): Maximum total price.
                max_products (int): Exact number of products to select.

            Returns:
                list: A list of selected product instances, or an empty list if no combination is found.
            """
            # Fetch all products and shuffle them for randomness
            products = list(Product.objects.filter(price__lte=max_amount))
            shuffle(products)  # Randomize the order of products

            # Use a generator to lazily produce combinations
            product_combinations = (combination for combination in combinations(products, max_products))

            # Iterate through combinations lazily
            for combination in product_combinations:
                # Calculate the total price for the combination
                total_price = sum(Decimal(product.price) for product in combination)

                # Check if total price falls within the specified range
                if min_amount <= total_price <= max_amount:
                    return list(combination)  # Return the first valid combination

            # If no valid combination is found, return an empty list
            return []


    class List(serializers.ModelSerializer):
        user = AdminUserUpdateSerializer.UserProfileRetrieve(read_only=True)
        number_of_negative_product = serializers.SerializerMethodField(read_only=True)
        rank_appearance = serializers.SerializerMethodField(read_only=True)
        on_hold = OnHoldPaySerializer(read_only=True)
        ref_name = "Negative User List"
        class Meta:
            model = Game
            fields = ['id','user','on_hold','number_of_negative_product','rank_appearance','is_active']
            ref_name = "Negative User List"

        def get_number_of_negative_product(self,obj):
            number_of_negative_product = obj.products.count()
            return number_of_negative_product

        def get_rank_appearance(self,obj):
            return obj.game_number