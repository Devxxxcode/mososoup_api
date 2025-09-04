from rest_framework.viewsets import ViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from .models import Deposit,PaymentMethod,Withdrawal
from .serializers import DepositSerializer,PaymentMethodSerializer,WithdrawalSerializer
from core.permissions import IsAdminOrReadCreateOnlyForRegularUsers
from shared.mixins import StandardResponseMixin
from shared.helpers import create_user_notification,create_admin_notification


class DepositViewSet(StandardResponseMixin, ViewSet):
    """
    ViewSet for managing deposits.
    - Admin users have full access to all deposits.
    - Regular users can only create deposits and view their own deposits.
    """
    permission_classes = [IsAuthenticated, IsAdminOrReadCreateOnlyForRegularUsers]
    parser_classes = [MultiPartParser, FormParser]

    def list(self, request):
        """
        List deposits made by the authenticated user.
        """
        if getattr(self, 'swagger_fake_view', False): 
            return Response([], status=status.HTTP_200_OK)
        
        user = request.user
        deposits = Deposit.objects.filter(user=user).order_by('-date_time')  # Regular user: Their deposits

        serializer = DepositSerializer(deposits, many=True)
        return self.standard_response(
            success=True,
            message="Deposits retrieved successfully.", 
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_description="Create a deposit for the authenticated user.",
        request_body=DepositSerializer,  # Use the DepositSerializer for the request body
        responses={
            201: openapi.Response(
                description="Deposit created successfully.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Deposit created successfully.",
                        "data": {
                            "id": 1,
                            "amount": "100.00",
                            "user": "username",
                            "status": "Pending",
                            "created_at": "2024-11-24T12:00:00Z",
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Validation error.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Validation failed.",
                        "data": {
                            "amount": ["This field is required."],
                        },
                    }
                },
            ),
        },
    )

    def create(self, request):
        """
        Create a deposit for the authenticated user.
        """
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, status="Pending")
        message = f"You made a deposit of {serializer.validated_data['amount']} USD"
        create_user_notification(
            user=request.user,
            title="Deposit",
            message=message
            )
        message = f"A new deposit of {serializer.validated_data['amount']} USD was initialized by {request.user.username}"
        create_admin_notification(
            "Deposit Created",
            message,
        )
        return self.standard_response(
            success=True,
            message="Deposit created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )



class PaymentMethodViewSet(StandardResponseMixin, ViewSet):
    """
    ViewSet for managing user payment methods.
    - Users can create, view, update, and delete their payment methods.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        List or create the authenticated user's payment method.
        """
        user = request.user

        # Use get_or_create to ensure a payment method exists
        payment_method, created = PaymentMethod.objects.get_or_create(
            user=user,
            defaults={
                "name": (
                    f"{user.first_name if user.first_name else ''} {user.last_name if user.last_name else ''}".strip()
                ) or user.username,
                "phone_number": getattr(user, "phone_number", ""),
                "email_address": user.email,
                "wallet": "",
                "exchange": ""
            }
        )

        # Ensure `name` is properly updated after creation
        if created:
            payment_method.name = (
                f"{user.first_name if user.first_name else ''} {user.last_name if user.last_name else ''}".strip()
            ) or user.username
            payment_method.save()

        serializer = PaymentMethodSerializer(payment_method)

        message = (
            "Payment method created successfully." if created else "Payment method retrieved successfully."
        )

        return self.standard_response(
            success=True,
            message=message,
            data=serializer.data,
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
    @swagger_auto_schema(
        operation_summary="Create or Update Payment Method",
        operation_description="Create or update the authenticated user's payment method.",
        request_body=PaymentMethodSerializer,
        responses={
            201: openapi.Response(
                description="Payment method created successfully.",
                schema=PaymentMethodSerializer
            ),
            200: openapi.Response(
                description="Payment method updated successfully.",
                schema=PaymentMethodSerializer
            ),
            400: "Validation error occurred.",
        }
    )
    def create(self, request):
        """
        Create or update the authenticated user's payment method.
        """
        # Use `get_or_create` to ensure a single payment method per user
        payment_method, created = PaymentMethod.objects.get_or_create(user=request.user)
        serializer = PaymentMethodSerializer(payment_method, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        create_user_notification(request.user,"Payment Method",f"Your Payment details has been updated successfully")
        create_admin_notification("Payment Method",f"{request.user.username} has updated is payment method")

        message = "Payment method created successfully." if created else "Payment method updated successfully."
        return self.standard_response(
            success=True,
            message=message,
            data=serializer.data,
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
    
class WithdrawalViewSet(StandardResponseMixin, ViewSet):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a withdrawal request for a user.",
        request_body=WithdrawalSerializer.MakeWithdrawal,
        responses={
            201: openapi.Response(
                description="Withdrawal request successfully created.",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Withdrawal Request Made Successfully.",
                        "data": {
                            "amount": "100.00",
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="Validation failed.",
                examples={
                    "application/json": {
                        "success": False,
                        "message": "Validation failed.",
                        "data": {
                            "amount": ["This field is required."],
                            "password": ["This field is required."]
                        },
                    }
                },
            ),
        },
    )
    @action(detail=False, methods=['post'])
    def make_withdrawal(self, request):
        """
        Handle withdrawal requests.
        """
        serializer = WithdrawalSerializer.MakeWithdrawal(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # Process the withdrawal logic here
        amount = serializer.validated_data['amount']
        
        # Assuming the user has a `payment_method` attribute
        payment_method = request.user.payment_method

        # Create the withdrawal record
        Withdrawal.objects.create(user=request.user, amount=amount, payment_method=payment_method)
        message = f"You made a withdrawal request of  {serializer.validated_data['amount']} USD"
        create_user_notification(
            user=request.user,
            title="Withdrawal",
            message=message
            )
        message = f"A new withdrawal of {serializer.validated_data['amount']} USD was initialized by {request.user.username}"
        create_admin_notification("Withdrawal",message)
        # Custom standard response
        return self.standard_response(
            success=True,
            message="Withdrawal Request Made Successfully.",
            data=serializer.validated_data,
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'])
    def withdrawal_history(self,request):
        """
        Retrieve the withdrawal history for the authenticated user.
        """
        withdrawals = Withdrawal.objects.filter(user=request.user)
        serializer = WithdrawalSerializer.ListWithdrawals(withdrawals, many=True)
        return self.standard_response(
            success=True,
            message="Withdrawal History Fetched succesfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )