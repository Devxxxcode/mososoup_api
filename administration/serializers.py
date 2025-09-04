from rest_framework import serializers
from .models import Settings,Event
from finances.models import Deposit,Withdrawal
from shared.helpers import get_settings
from users.models import Invitation
# from users.serializers import UserPartialSerilzer
from shared.helpers import create_user_notification
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        exclude = ['id']

    def to_representation(self, instance):
        """
        Customize the representation of the video field to return the .url.
        """
        representation = super().to_representation(instance)
        # Replace the video field with its URL
        if instance.video:
            representation['video'] = instance.video.url
        return representation


class SettingsVideoSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the video field in the Settings model.
    """
    
    class Meta:
        model = Settings
        fields = ['video']  # Include only the video field

    def to_representation(self, instance):
        """
        Customize the representation of the video field to return the .url.
        """
        representation = super().to_representation(instance)
        # Replace the video field with its URL
        if instance.video:
            representation['video'] = instance.video.url
        return representation

    def validate_video(self, value):
        if not value.name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            raise serializers.ValidationError("The uploaded file is not a valid video format.")
        return value

class UserPartialSerializer(serializers.ModelSerializer):
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

class DepositSerializer:
    """
    Container for different Deposit serializers used in various actions.
    """

    class List(serializers.ModelSerializer):
        """
        Serializer for listing deposits.
        """
        user = UserPartialSerializer(read_only=True)
        class Meta:
            model = Deposit
            fields = "__all__"
            ref_name = "Deposit - List"

    class UpdateStatus(serializers.ModelSerializer):
        """
        Serializer for updating the status of a deposit.
        """
        admin_password = serializers.CharField(write_only=True,required=True)

        class Meta:
            model = Deposit
            fields = [
                "status",
                "admin_password",
            ]
            ref_name = "Deposit - UpdateStatus"

        def validate_admin_password(self, value):
            """
            Validate the transactional password from the user.
            """
            user = self.context.get("request").user
            if not user.check_transactional_password(value):
                raise serializers.ValidationError("Incorrect admin password.")
            if not user.is_staff:
                raise serializers.ValidationError("User does not have permission to perform this action.")
            return value

        def validate_status(self, value):
            """
            Validate the status field.
            """
            allowed_statuses = ["Pending", "Confirmed", "Rejected"]
            if value not in allowed_statuses:
                raise serializers.ValidationError(f"Invalid status: {value}. Allowed: {allowed_statuses}")
            return value

        def update(self, instance, validated_data):
            """
            Update the deposit status and adjust the user's wallet balance based on the status transition.
            """
            old_status = instance.status
            new_status = validated_data.get("status")

            # Update the deposit instance
            instance.status = new_status
            instance.save()

            user = instance.user

            self.adjust_wallet_balance(
                user=instance.user,
                amount=instance.amount,
                old_status=old_status,
                new_status=new_status,
            )

            return instance

        def adjust_wallet_balance(self, user, amount, old_status, new_status):
            """
            Adjust the user's wallet balance based on status changes.
            """
            if old_status != "Confirmed" and new_status == "Confirmed":
                # Increment wallet balance when status changes to Confirmed
                user.wallet.credit(amount)
                user.wallet.save()
                # self.handle_referral_bonus(user,amount)
                create_user_notification(
                    user,"Deposit Update",f"Your deposit of {amount} USD has validated. New Balance is {user.wallet.balance} USD"
                )
                print(f"Wallet increased: User {user.id} balance is now {user.wallet.balance}")

            elif old_status == "Confirmed" and new_status != "Confirmed":
                # Decrement wallet balance when status changes from Confirmed
                user.wallet.balance -= amount
                user.wallet.save()
                print(f"Wallet decreased: User {user.id} balance is now {user.wallet.balance}")
                create_user_notification(
                    user,"Deposit Update",f"Your deposit of {amount} USD has been Cancelled. New Balance is {user.wallet.balance} USD"
                )
            else:
                create_user_notification(
                    user,"Deposit Update",f"Your deposit of {amount} USD has been Rejected. New Balance is {user.wallet.balance} USD"
                )

        def handle_referral_bonus(self, user, amount):
            """
            Check if the user has an associated invitation and award the referral bonus if applicable.
            """
            try:
                # Retrieve the invitation for the user
                invitation = user.invitation  # Access the Invitation instance associated with the user
                if not invitation.received_bonus:
                    # Retrieve settings to calculate the bonus percentage
                    settings = get_settings()
                    bonus_percentage = Decimal(settings.percentage_of_sponsors)  # Ensure it's Decimal
                    bonus_amount = amount * (bonus_percentage / Decimal(100))  # Use Decimal for calculation

                    # Award the referral bonus to the referrer
                    referral = invitation.referral
                    referral.wallet.balance += bonus_amount
                    referral.wallet.save()

                    # Mark the bonus as received
                    invitation.received_bonus = True
                    invitation.save()
                    create_user_notification(
                        referral,
                        "Referral Bonus",
                        f"You have received a referral bonus of {bonus_amount:.2f}. Your current balance is {referral.wallet.balance}"
                    )
                    print(f"Referral bonus of {bonus_amount:.2f} awarded to user {referral.username} (ID: {referral.id}).")
            except Invitation.DoesNotExist:
                # Handle case where no invitation is found
                print(f"No invitation found for user {user.username}.")


class EventSerializer(serializers.ModelSerializer):
    created_by = UserPartialSerializer(read_only=True)
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'image', 'is_active', 'created_at','created_by']
        read_only_fields = ['created_at','created_by']

    def save(self, **kwargs):
        """
        Automatically set the `created_by` field to the currently logged-in user for both creation and update.
        """
        kwargs['created_by'] = self.context['request'].user
        return super().save(**kwargs)


class WithdrawalSerializer:
    """
    Container for different Withdrawal serializers used in various actions.
    """

    class List(serializers.ModelSerializer):
        """
        Serializer for listing withdrawals.
        """
        user = UserPartialSerializer(read_only=True)
        class Meta:
            model = Withdrawal
            fields = "__all__"
            ref_name = "Withdrawal - List"
            

    class UpdateStatus(serializers.ModelSerializer):
        """
        Serializer for updating the status of a withdrawal.
        """
        class Meta:
            model = Withdrawal
            fields = [
                "status",
            ]
            ref_name = "Withdrawal - UpdateStatus"

        def validate_status(self, value):
            """
            Validate the status field.
            """
            allowed_statuses = ["Processed", "Rejected"]
            if value not in allowed_statuses:
                raise serializers.ValidationError(f"Invalid status: {value}. Allowed: {allowed_statuses}")
            return value


        def update(self, instance, validated_data):
            """
            Update the withdrawal status and adjust the user's wallet balance based on the status transition.
            """
            if instance.is_reviewed:
                raise serializers.ValidationError({"error": "The withdrawal status has been processed before."})
            
            old_status = instance.status
            new_status = validated_data.get("status")

            # Ensure the new status is valid
            allowed_statuses = ["Processed", "Rejected"]
            if new_status not in allowed_statuses:
                raise serializers.ValidationError({"error": f"Invalid status: {new_status}. Allowed statuses are: {allowed_statuses}"})

            # Update the withdrawal instance
            instance.status = new_status
            instance.is_reviewed = True
            instance.save()

            user = instance.user

            self.adjust_wallet_balance(
                user=instance.user,
                amount=instance.amount,
                old_status=old_status,
                new_status=new_status,
            )

            self.notify_user_on_status_change(user,new_status,instance.amount)

            return instance


        def adjust_wallet_balance(self, user, amount, old_status, new_status):
            """
            Adjust the user's wallet balance based on status changes.
            """
            if old_status != "Processed" and new_status == "Processed":
                # Decrement wallet balance when status changes to Processed
                print(f"Wallet decreased: User {user.id} balance is now {user.wallet.balance}")
                # create_user_notification(
                #     user,"Withdrawal Update",f"Your Withdrawal of {amount} USD has been Processed."
                # )
                user.wallet.balance -= amount
                user.wallet.save()

            elif old_status == "Processed" and new_status != "Processed":
                # Increment wallet balance when status changes from Processed (rollback)
                user.wallet.balance += amount
                user.wallet.save()
                print(f"Wallet increased: User {user.id} balance is now {user.wallet.balance}")
                # create_user_notification(
                #     user,"Withdrawal Update",f"Your Withdrawal of {amount} USD has been Rejected."
                # )

        def notify_user_on_status_change(self, user, new_status, amount):
            """
            Notify the user of the withdrawal status change, including their new balance if rejected.
            """
            if new_status == "Rejected":
                message = (
                    f"Your withdrawal request of {amount:.2f} USD has been rejected. "
                    f"Your current balance is now {user.wallet.balance:.2f} USD."
                )
            elif new_status == "Processed":
                message = f"Your withdrawal request of {amount:.2f} USD has been processed successfully. Your current balance is now {user.wallet.balance:.2f} USD."
            elif new_status == "Pending":
                message = f"Your withdrawal request of {amount:.2f} USD is pending."
            else:
                message = f"Your withdrawal status has been updated to {new_status.lower()}."

            # Send notification to the user
            create_user_notification(user, "Withdrawal Status Update", message)