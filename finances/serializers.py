from rest_framework import serializers
from .models import Deposit,PaymentMethod,Withdrawal
from django.contrib.auth  import get_user_model

User = get_user_model()

class UserPartialSerilzer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "last_name",
            "first_name",
            "is_active"
        ]


class DepositSerializer(serializers.ModelSerializer):
    # from users.serializers import UserPartialSerilzer
    # user = UserPartialSerilzer(read_only=True)  # Display the username instead of the ID

    class Meta:
        model = Deposit
        fields = [
            "id", "user", "amount", "date_time", "status", "screenshot", 
            "created_at", "updated_at"
        ]
        read_only_fields = ["user", "created_at", "updated_at",'status']

class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentMethod with user details mapping.
    """
    name = serializers.CharField(read_only=True) 
    phone_number = serializers.CharField(read_only=True) 
    email_address = serializers.CharField(read_only=True) 

    class Meta:
        model = PaymentMethod
        fields = "__all__"
        read_only_fields = ["name", "phone_number", "email_address",'user'] 

    def save(self, **kwargs):
        """
        Save method to map user details into the PaymentMethod instance.
        """
        user = kwargs.get("user")  # Get the user from the context or kwargs
        instance = super().save(**kwargs)

        # Map user details into the PaymentMethod fields
        if user:
            instance.name = f"{user.first_name if user.first_name else ''} {user.last_name if user.last_name else ''}".strip() or user.username
            instance.phone_number = getattr(user, "phone_number", None)
            instance.email_address = user.email
            instance.save()

        return instance


class WithdrawalSerializer:

    class MakeWithdrawal(serializers.ModelSerializer):
        amount = serializers.DecimalField(max_digits=10, decimal_places=2)
        password = serializers.CharField(write_only=True)  # Password should not be exposed in the response

        class Meta:
            model = Withdrawal
            fields = ["amount", "password"]

        def validate(self, data):
            data = super().validate(data)  # Ensure base validation logic is executed
            user = self.context['request'].user  # Access request.user from context
            
            if not user.is_authenticated:
                raise serializers.ValidationError("User is not authenticated.")

            # Call the can_withdraw method on the Withdrawal model
            can_withdraw, error = Withdrawal.can_withdraw(user, data["amount"], data["password"])
            
            if not can_withdraw:
                raise serializers.ValidationError({"error":error})
            
            # user_wallet = user.wallet
            # if user_wallet:
            #     user_wallet.debit(data['amount'])

            data.pop("password","")
            return data
        
    class ListWithdrawals(serializers.ModelSerializer):
        payment_method = PaymentMethodSerializer(read_only=True)
        class Meta:
            model = Withdrawal
            fields = "__all__"