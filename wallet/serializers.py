from .models import Wallet,OnHoldPay
from rest_framework import serializers
from packs.serializers import PackProfileSerializer,PackSerializer

class WalletSerializer:

    class UserWalletSerializer(serializers.ModelSerializer):
        package = PackProfileSerializer(read_only=True)
        """
        Serializer for Wallet model.
        """
        class Meta:
            model = Wallet
            fields = ["balance","on_hold","commission","salary",'package','credit_score'] 
            ref_name = 'WalletSerializer 1'


    class AdminUserWalletSerializer(serializers.ModelSerializer):
        package = PackSerializer(read_only=True)
        class Meta:
            model = Wallet
            fields = "__all__"
            ref_name = "WalletSerializer 2"

class OnHoldPaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OnHoldPay
        fields = ['id','min_amount','max_amount','is_active']
        ref_name = "OnHoldPaySerializer walltet 2"