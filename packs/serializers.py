from rest_framework import serializers
from .models import Pack
from administration.serializers import UserPartialSerializer

class PackSerializer(serializers.ModelSerializer):
    created_by = UserPartialSerializer(read_only=True)
    minimum_balance_for_submissions = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, min_value=0)
    class Meta:
        model = Pack
        fields = [
            "id", "name", "usd_value", "daily_missions","short_description", 'description',
            "daily_withdrawals", "icon", "created_by", "is_active", 
            "created_at", "updated_at",'payment_limit_to_trigger_bonus','payment_bonus','profit_percentage','special_product_percentage','number_of_set',
            "minimum_balance_for_submissions"
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def save(self, **kwargs):
        
        # Set created_by to the current user if provided
        user = self.context['request'].user
        kwargs['created_by'] = user
        return super().save(**kwargs)

class PackProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pack
        fields = ["id","name","icon","usd_value","number_of_set"]
