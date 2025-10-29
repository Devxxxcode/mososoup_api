from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

from .models import Invitation,InvitationCode
from wallet.models import Wallet,OnHoldPay
from wallet.serializers import WalletSerializer
from administration.serializers import SettingsSerializer
from shared.helpers import get_settings
from shared.mixins import AdminPasswordMixin
from game.models import Product,Game
from django.utils.timezone import now, timedelta
from django.db.models import Q
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models import Count
from finances.models import PaymentMethod
from finances.serializers import PaymentMethodSerializer
import random
from shared.helpers import create_user_notification



User = get_user_model()


class BaseAuthSerializer(serializers.Serializer):
    def validate(self, attrs):
        # Ensure username_or_email and password are not empty
        if not attrs.get('username_or_email'):
            raise serializers.ValidationError({"username_or_email": "This field is required."})
        if not attrs.get('password'):
            raise serializers.ValidationError({"password": "This field is required."})
        return attrs

class UserSignupSerializer(serializers.ModelSerializer):
    invitation_code = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'first_name', 'last_name', 'gender', 'transactional_password','invitation_code','referral_code','profile_picture']
        extra_kwargs = {
            'password': {'write_only': True},
            'transactional_password': {'write_only': True}
        }
        read_only_fields = ['referral_code','profile_picture']

    def validate_email(self, value):
        """
        Validate and normalize the email address.
        """
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        return email

    def validate_transactional_password(self,value):
        if len(value) < 4:
            raise serializers.ValidationError("The transactional password must be exactly 4 characters long")
        if len(value) != 4:
            raise serializers.ValidationError("The transactional password must be exactly 4 characters long")
        return value


    def validate_username(self, value):
        """
        Validate the username for uniqueness.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError({"username": "A user with this username already exists."})
        return value
    
    def validate_invitation_code(self, value):
        """
        Validate the invitation code.
        """
        # Prefer a tolerant lookup to avoid MultipleObjectsReturned when referral_code isn't unique
        referrer = User.objects.filter(referral_code=value).first()
        if referrer:
            return referrer
        else:
            try:
                code = InvitationCode.objects.get(invitation_code=value)
                if code.is_used:
                    raise serializers.ValidationError("The invitation code has been used")
                else:
                    return code
            except InvitationCode.DoesNotExist:
                raise serializers.ValidationError("Invalid invitation code.")

    def create(self, validated_data):
        """
        Create a new user with the validated data.
        """
        password = validated_data.pop('password')

        referrer = validated_data.pop('invitation_code')
        
        user = User.objects.create_user(password=password, **validated_data)

        # Create the invitation entry
        if isinstance(referrer,User):
            Invitation.objects.create(referral=referrer, user=user)
        if isinstance(referrer, InvitationCode):
            referrer.is_used = True
            referrer.save()

        return user


class UserLoginSerializer(BaseAuthSerializer, serializers.ModelSerializer):
    username_or_email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username_or_email', 'password']

    def validate(self, attrs):
        # Call the validation logic from BaseAuthSerializer
        attrs = super().validate(attrs)

        # Perform authentication logic or any additional validation
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')

        # Add your authentication logic here (example)
        user = authenticate(username=username_or_email, password=password)
        if user is None:
            raise serializers.ValidationError({"username_or_email": "Invalid credentials."})
        if not user.is_active:
            raise serializers.ValidationError({"username_or_email": "Your account is currently is inactive."})

        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer.UserWalletSerializer(read_only=True) 
    settings = serializers.SerializerMethodField(read_only=True)
    total_number_can_play = serializers.SerializerMethodField()
    current_number_count = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id','username','email','phone_number','first_name','last_name','gender','referral_code','profile_picture','last_connection','is_active','date_joined','wallet','settings','today_profit','total_number_can_play','current_number_count']
        read_only_fields = ['date_joined','referral_code']
        ref_name = "UserProfileSerializer "

    def get_total_number_can_play(self,obj):
        wallet = getattr(obj, 'wallet', None)
        if not wallet:
            wallet = Wallet.objects.create(user=obj)

        total_number_can_play = wallet.package.daily_missions  # Example: Maximum number of games per day
        return total_number_can_play
    
    def get_current_number_count(self,obj):
        return obj.number_of_submission_today
    
    def get_settings(self,obj):
        instance = get_settings()
        if not instance:
            raise NotFound(detail="Settings not found.")
        serializer = SettingsSerializer(instance=instance)
        return serializer.data

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


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """
        Validate the current password.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        """
        Validate the new password (add strength checks if needed).
        """
        # Example of a custom password strength check
        if len(value) < 1:
            raise serializers.ValidationError("New password can not be empty")
        return value

    def save(self):
        """
        Update the user's password.
        """
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()


class ChangeTransactionalPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """
        Validate the current password.
        """
        user = self.context['request'].user
        if not user.check_transactional_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    def validate_new_password(self, value):
        """
        Validate the new password (add strength checks if needed).
        """
        # Example of a custom password strength check
        if len(value) < 4:
            raise serializers.ValidationError("The new password must be at least 4 characters long.")
        if len(value) != 4:
            raise serializers.ValidationError("The transactional password must be exactly 4 characters long")
        return value

    def save(self):
        """
        Update the user's password.
        """
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.transactional_password = new_password
        user.save()


class InvitationCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitationCode
        fields = ['id', 'invitation_code', 'is_used', 'created_at'] 



class UserProfileListSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer.UserWalletSerializer(read_only=True) 
    total_play = serializers.SerializerMethodField(read_only=True)
    total_available_play = serializers.SerializerMethodField(read_only=True)
    total_product_submitted = serializers.SerializerMethodField(read_only=True)
    total_negative_product_submitted = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = User
        fields = ['id','username','email','phone_number','first_name','last_name','gender','referral_code','profile_picture','last_connection','is_active','date_joined','wallet','total_play','total_available_play','total_product_submitted','total_negative_product_submitted','is_min_balance_for_submission_removed','is_reg_balance_add','number_of_submission_set_today','today_profit']
        read_only_fields = ['date_joined','referral_code',]

    def get_total_play(self,obj):
        return Game.count_games_played_today(obj)

    def get_total_available_play(self,obj):
        try:
            wallet = obj.wallet
            return wallet.package.daily_missions
        except Wallet.DoesNotExist:
            return None

    def get_total_negative_product_submitted(self,obj):
        return Game.objects.filter(user=obj,special_product=True,played=True,is_active=True).count()

    def get_total_product_submitted(self,obj):
        return Game.objects.filter(user=obj,played=True,is_active=True).count()


# ----------------------------------- Admin Serializers -----------------------------------------

class DashboardSerializer(serializers.Serializer):
    """
    Serializer for admin dashboard data.
    """
    total_users = serializers.SerializerMethodField()
    active_products = serializers.SerializerMethodField()
    total_submissions = serializers.SerializerMethodField()
    total_users_login_today = serializers.SerializerMethodField()
    user_registrations_per_month = serializers.SerializerMethodField()
    total_submissions_per_month = serializers.SerializerMethodField()

    def get_total_users(self, obj):
        # Replace with actual logic to calculate total users
        return User.objects.users().count()

    def get_active_products(self, obj):
        # Replace with actual logic to calculate active users
        return Product.objects.count()

    def get_total_submissions(self, obj):
        # Calculate the start of today
        start_of_today = now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_today = start_of_today + timedelta(days=1)

        # Query to count games created today with `played=True` or `pending=True`
        count = Game.objects.filter(
            updated_at__gte=start_of_today,  # From start of today
            updated_at__lt=end_of_today,    # Until the end of today
            is_active=True
        ).filter(
            Q(played=True) | Q(pending=True)  # Either played or pending
        ).count()
        return count
    
    def get_total_users_login_today(self, obj):
        """
        Count the total number of users who logged in today based on their `last_connection` field.
        """
        # Calculate the start and end of today
        start_of_today = now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_today = start_of_today + timedelta(days=1)

        # Filter users whose last_connection is within today's range
        users_today = User.objects.filter(
            last_connection__gte=start_of_today,
            last_connection__lt=end_of_today,
        ).order_by("-last_connection")  # Most recent first

        return {
            "count": users_today.count(),
            "users": UserProfileListSerializer(users_today, many=True).data  # Serialize user list
        }

    def get_user_registrations_per_month(self, obj):
        """
        Get the number of users registered per month for the current year,
        up to the current month.
        """
        current_year = now().year
        current_month = now().month

        # Aggregate data grouped by month
        registrations = User.objects.users().filter(
            date_joined__year=current_year
        ).annotate(
            month=ExtractMonth('date_joined')  # Extract month from date_joined
        ).values(
            'month'
        ).annotate(
            count=Count('id')  # Count users for each month
        ).order_by('month')

        # Initialize all months with 0
        result = {month: 0 for month in range(1, 13)}

        # Update result with actual counts
        for reg in registrations:
            result[reg['month']] = reg['count']

        return result
        
        
    def get_total_submissions_per_month(self, obj):
        """
        Get the total number of submissions per month for the current year.
        Includes submissions where played=True or pending=True.
        """
        current_year = now().year
        current_month = now().month

        # Query for submissions grouped by month
        submissions = Game.objects.filter(
            updated_at__year=current_year,  # Filter by current year
            is_active=True
        ).filter(
            Q(played=True) | Q(pending=True)  # Filter for played or pending
        ).annotate(
            month=ExtractMonth('updated_at')  # Group by month
        ).values(
            'month'
        ).annotate(
            count=Count('id')  # Count games for each month
        ).order_by('month')

        # Format the result for only the months up to the current month
        result = {month: 0 for month in range(1, current_month + 1)}
        for submission in submissions:
            if submission['month'] <= current_month:  # Ensure only months up to the current month are included
                result[submission['month']] = submission['count']

        return result


class AdminAuthSerializer:

    class Login(UserLoginSerializer):
        """
        Serializer for admin login, ensuring only staff users can authenticate.
        """

        def validate(self, attrs):
            # Call the base class validate method to perform the standard validation
            attrs = super().validate(attrs)

            # Additional validation for admin users
            user = attrs.get('user')
            if not user.is_staff:
                raise serializers.ValidationError({"username_or_email": "Access restricted to admin users only."})

            return attrs
    
    class Write(serializers.ModelSerializer):
        """
        Serializer for creating or updating admin users.
        """

        class Meta:
            model = User
            fields = ['id', 'username', 'email', 'is_staff', 'is_active','phone_number','first_name','last_name','profile_picture']
            read_only_fields = ['is_staff', 'is_active']
            ref_name = "Admin User - Write"

    class List(Write):
        dashboard = DashboardSerializer(source='*')
        """
        Serializer for listing admin users.
        """
        class Meta:
            model = User
            fields = ['id', 'username', 'email', 'is_staff', 'is_active','phone_number','first_name','last_name','profile_picture','dashboard']
            ref_name = "Admin User - List"



class AdminUserUpdateSerializer:

    class LoginPassword(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        password = serializers.CharField(write_only=True, required=True)

        def save(self):
            """
            Update the password of the user.
            """
            user = self.validated_data['user']  # This will give you the user instance
            new_password = self.validated_data['password']
            user.set_password(new_password)
            user.save()
            return user
        
    class WithdrawalPassword(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        password = serializers.CharField(write_only=True, required=True)

        def save(self):
            """
            Update the password of the user.
            """
            user = self.validated_data['user']  # This will give you the user instance
            new_password = self.validated_data['password']
            user.transactional_password = new_password
            user.save()
            return user
        
    class UserBalance(AdminPasswordMixin,serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        balance = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
        reason = serializers.CharField(required=True)

        def save(self):
            """
            Update the balance for the given user and record the reason.
            """
            user = self.validated_data['user']
            new_balance = self.validated_data['balance']
            reason = self.validated_data['reason']
            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)
            # Use credit to properly clear negatives and release on_hold
            wallet.credit(new_balance)
            user.save()
            create_user_notification(user,"Admin Update User",f"Your Balance had been Updated with {new_balance} USD, New Balance {wallet.balance} USD")
            return user

    class UserBalanceCalculation(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        balance_adjustment = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

        def calculate_resulting_balance(self):
            """
            Calculate what the resulting balance would be without saving it.
            Uses the credit method logic to handle negative balances and on_hold funds.
            """
            user = self.validated_data['user']
            balance_adjustment = self.validated_data['balance_adjustment']
            
            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)
            
            # Create a copy of the wallet to simulate the calculation
            from copy import deepcopy
            simulated_wallet = deepcopy(wallet)
            
            # Apply the credit method logic without saving
            current_balance = simulated_wallet.balance
            current_on_hold = simulated_wallet.on_hold
            
            # Simulate the credit method logic
            if current_balance < 0:
                if balance_adjustment >= abs(current_balance):
                    # Clear entire negative balance and add remaining to balance
                    remaining_amount = balance_adjustment - abs(current_balance)
                    resulting_balance = remaining_amount
                else:
                    # Partial clear of negative balance
                    resulting_balance = current_balance + balance_adjustment
            else:
                # Normal deposit - add amount to balance
                resulting_balance = current_balance + balance_adjustment
            
            # If balance is now non-negative and on_hold exists, move on_hold to balance
            if resulting_balance >= 0 and current_on_hold > 0:
                resulting_balance += current_on_hold
                resulting_on_hold = 0
            else:
                resulting_on_hold = current_on_hold
            
            return {
                'current_balance': current_balance,
                'current_on_hold': current_on_hold,
                'balance_adjustment': balance_adjustment,
                'resulting_balance': resulting_balance,
                'resulting_on_hold': resulting_on_hold,
                'negative_balance_cleared': current_balance < 0 and resulting_balance >= 0,
                'on_hold_moved_to_balance': current_on_hold > 0 and resulting_on_hold == 0 and resulting_balance >= 0
            }

    class UserProfitCalculation(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        profit_adjustment = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

        def calculate_resulting_profit(self):
            """
            Calculate what the resulting profit would be without saving it.
            """
            user = self.validated_data['user']
            profit_adjustment = self.validated_data['profit_adjustment']

            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)

            current_profit = user.today_profit or 0
            current_commission = wallet.commission or 0
            
            # Calculate the difference and resulting values
            profit_diff = profit_adjustment - current_profit
            resulting_profit = profit_adjustment
            resulting_commission = current_commission + profit_diff

            return {
                'current_profit': current_profit,
                'current_commission': current_commission,
                'profit_adjustment': profit_adjustment,
                'profit_difference': profit_diff,
                'resulting_profit': resulting_profit,
                'resulting_commission': resulting_commission,
                'commission_will_increase': profit_diff > 0,
                'commission_will_decrease': profit_diff < 0
            }

    class UserSalaryCalculation(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        salary_adjustment = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

        def calculate_resulting_salary(self):
            """
            Calculate what the resulting salary and balance would be without saving it.
            """
            user = self.validated_data['user']
            salary_adjustment = self.validated_data['salary_adjustment']

            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)

            current_salary = wallet.salary or 0
            current_balance = wallet.balance or 0
            
            # Calculate the difference and resulting values
            salary_diff = salary_adjustment - current_salary
            resulting_salary = salary_adjustment
            resulting_balance = current_balance + salary_diff

            return {
                'current_salary': current_salary,
                'current_balance': current_balance,
                'salary_adjustment': salary_adjustment,
                'salary_difference': salary_diff,
                'resulting_salary': resulting_salary,
                'resulting_balance': resulting_balance,
                'balance_will_increase': salary_diff > 0,
                'balance_will_decrease': salary_diff < 0
            }
        
    class UserProfit(AdminPasswordMixin,serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        profit = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
        reason = serializers.CharField(required=True)

        def save(self):
            """
            Update the balance for the given user and record the reason.
            """
            user = self.validated_data['user']
            new_balance = self.validated_data['profit']
            reason = self.validated_data['reason']
            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)
            old_profit = user.today_profit
            user.today_profit = new_balance
            diff = new_balance - old_profit
            # Update commission by the difference (increase/decrease)
            if diff >= 0:
                wallet.credit_commission(diff)
            else:
                wallet.debit_commission(abs(diff))
            user.save()
            # create_user_notification(user,"Admin Update User",f"Your Today Profit has been Updated with {diff} USD, New Balance {wallet.balance} USD")
            return user
        
    class UserSalary(AdminPasswordMixin,serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        salary = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
        reason = serializers.CharField(required=True)

        def save(self):
            """
            Update the salary for the given user and record the reason.
            """
            user = self.validated_data['user']
            new_balance = self.validated_data['salary']
            reason = self.validated_data['reason']
            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)
            old_salary = wallet.salary
            wallet.salary = new_balance
            diff = new_balance - old_salary
            user.save()
            # Apply salary difference to balance via credit (handles negatives/on_hold)
            if diff >= 0:
                wallet.credit(diff)
            else:
                # For salary decrease, reduce balance directly without triggering on_hold
                wallet.balance += diff  # diff is negative
                wallet.save()
            create_user_notification(user,"Admin Update User",f"Your Salary has been Updated with {diff} USD, New Balance {wallet.balance} USD")
            return user

    class UserProfile(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)

        def save(self):
            """
            Get all the user datails
            """
            user = self.validated_data['user']

            return user
        
    class UserProfileRetrieve(UserProfileListSerializer):
        use_payment_method = serializers.SerializerMethodField(read_only=True)

        class Meta:
            model = User
            fields = "__all__"
            ref_name = "Admin User Retrieve"
            extra_kwargs = {
            'password': {'write_only': True},
            'transactional_password': {'write_only': True}
        }
            

        def get_use_payment_method(self,obj):
            try:
                method = obj.payment_method
            except PaymentMethod.DoesNotExist:
                method = PaymentMethod.objects.create(user=obj)

            return PaymentMethodSerializer(instance=method).data

    class SetUserPack(AdminPasswordMixin, serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)
        pack_id = serializers.IntegerField(required=True)

        def validate(self, attrs):
            attrs = super().validate(attrs)
            from packs.models import Pack
            # First, validate that the pack exists
            try:
                pack = Pack.objects.get(id=attrs['pack_id'])
            except Pack.DoesNotExist:
                raise serializers.ValidationError({"pack_id": "Selected pack does not exist."})

            # Then, ensure the pack is active
            if not pack.is_active:
                raise serializers.ValidationError({"pack_id": "Selected pack is inactive. Please choose an active pack."})

            attrs['pack'] = pack
            return attrs

        def save(self):
            user = self.validated_data['user']
            pack = self.validated_data['pack']
            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)
            wallet.package = pack
            wallet.save(update_fields=["package", "updated_at"])
            create_user_notification(user, "Package Updated", f"Your membership pack has been set to {pack.name}.")
            return user

    class ToggleRegBonus(AdminPasswordMixin,serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)

        def save(self):
            """
            Get all the user datails
            """
            user = self.validated_data['user']
            if user.is_reg_balance_add:
                # Remove registration bonus: reduce balance safely without triggering on_hold
                new_balance = user.wallet.balance - user.reg_balance_amount
                user.is_reg_balance_add = False
                user.wallet.balance = new_balance
                user.wallet.save()
                
            else:
                # Add registration bonus: use credit to properly handle negatives/on_hold
                user.wallet.credit(user.reg_balance_amount)
                new_balance = user.wallet.balance
                user.is_reg_balance_add = True
                user.wallet.save()

            user.save()
            
            return user
        
    class ToggleUserMinBalanceForSubmission(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)

        def save(self):
            """
            Toggle User Min Balance Settings
            """
            user = self.validated_data['user']
            if user.is_min_balance_for_submission_removed:
                user.is_min_balance_for_submission_removed = False
            else:
                user.is_min_balance_for_submission_removed = True

            user.save()
            message = f"Minimum Balanace for submission Has been Enabled" if  user.is_min_balance_for_submission_removed else f"Minimum Balanace for submission Has been Disabled"
            create_user_notification(user,"Admin Update",message)
            return user

    class ToggleUserActive(serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)

        def save(self):
            """
            Toggle User is_active status
            """
            user = self.validated_data['user']
            user.is_active = not user.is_active
            user.save()
            return user

    class ResetUserAccount(AdminPasswordMixin,serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        submission_count = serializers.IntegerField(
            required=False, 
            allow_null=True,
            min_value=0,
            help_text="Optional: Set the number of submissions today (0 to package daily_missions)"
        )
        set_count = serializers.IntegerField(
            required=False, 
            allow_null=True,
            min_value=0,
            help_text="Optional: Set the number of sets completed today (0 to package number_of_set)"
        )

        def validate(self, data):
            """
            Validate the submission_count and set_count against user's package limits
            """
            user = data.get('user')
            submission_count = data.get('submission_count')
            set_count = data.get('set_count')
            
            if not user:
                return data
                
            # Get user's package
            if not hasattr(user, 'wallet') or not user.wallet.package:
                raise serializers.ValidationError("User does not have a valid package assigned.")
            
            package = user.wallet.package
            
            # Validate submission_count
            if submission_count is not None:
                if submission_count > package.daily_missions:
                    raise serializers.ValidationError({
                        'submission_count': f"Submission count cannot exceed package daily missions limit ({package.daily_missions})"
                    })
            
            # Validate set_count
            if set_count is not None:
                if set_count > package.number_of_set:
                    raise serializers.ValidationError({
                        'set_count': f"Set count cannot exceed package number of sets limit ({package.number_of_set})"
                    })
            
            return data

        def save(self):
            """
            Reset User Account with optional custom values
            """
            user = self.validated_data['user']
            submission_count = self.validated_data.get('submission_count')
            set_count = self.validated_data.get('set_count')
            
            # Reset submission count
            if submission_count is not None:
                user.number_of_submission_today = submission_count
            else:
                # Default behavior: reset to 0
                user.number_of_submission_today = 0
            
            # Reset set count
            if set_count is not None:
                user.number_of_submission_set_today = set_count
            else:
                # Default behavior: reset to 0 if user has completed their set
                if user.number_of_submission_set_today >= user.wallet.package.number_of_set:
                    user.number_of_submission_set_today = 0
            
            # Send notification
            create_user_notification(
                user,
                "Account Reset",
                "Your account has been successfully reset, Proceed to make your submissions"
            )
            
            user.save()
            return user

    class UpdateUserCeditScore(AdminPasswordMixin,serializers.Serializer):
        user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),required=True)
        credit_score = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

        def save(self):
            """
            Update the user credit score
            """
            user = self.validated_data['user']
            new_score = self.validated_data['credit_score']
            try:
                wallet = user.wallet
            except Wallet.DoesNotExist:
                wallet = Wallet.objects.create(user=user)
            wallet.credit_score = new_score
            wallet.save()
            create_user_notification(user,"Admin Update User",f"Your Credit score has been updated to {new_score}%")
            return user

        def validate_credit_score(self, value):
            if not (0 <= value <= 100):
                raise serializers.ValidationError({'credit_score':"Credit score must be between 0 and 100."})
            return value
            


