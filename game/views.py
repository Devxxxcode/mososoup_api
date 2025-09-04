from rest_framework.viewsets import ModelViewSet,ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly,IsAuthenticated
from .models import Product
from rest_framework.decorators import action
from rest_framework import status
from .models import Game
from .serializers import ProductSerializer,GameSerializer
from shared.mixins import StandardResponseMixin
from core.permissions import IsAdminOrReadOnly
from .services import PlayGameService
from wallet.models import Wallet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from administration.models import Event
from administration.serializers import EventSerializer
from shared.helpers import create_admin_log


class ProductViewSet(StandardResponseMixin, ModelViewSet):
    """
    ViewSet for managing Product objects with standardized responses.
    """
    queryset = Product.objects.all().order_by('-date_created')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        product = serializer.save()
        try:
            create_admin_log(self.request, f"Created product '{product.name}' (USD {product.price})")
        except Exception:
            pass

    def perform_update(self, serializer):
        product = serializer.save()
        try:
            create_admin_log(self.request, f"Updated product '{product.name}' (USD {product.price})")
        except Exception:
            pass

    def perform_destroy(self, instance):
        name = instance.name
        price = instance.price
        super().perform_destroy(instance)
        try:
            create_admin_log(self.request, f"Deleted product '{name}' (USD {price})")
        except Exception:
            pass

    @action(detail=False, methods=['delete'], url_path='delete-all-products', permission_classes=[])
    def delete_all_products(self, request):
        """
        Delete all products in the database. No authentication required.
        WARNING: This will permanently delete ALL products!
        """
        try:
            # Get count before deletion for logging
            total_products = Product.objects.count()
            
            # Delete all products
            deleted_count = Product.objects.all().delete()[0]
            
            return self.standard_response(
                success=True,
                message=f"Successfully deleted {deleted_count} products from the database",
                data={
                    "deleted_count": deleted_count,
                    "total_products_before_deletion": total_products
                },
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return self.standard_response(
                success=False,
                message=f"Error deleting products: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GameViewSet(StandardResponseMixin, ViewSet):
    """
    ViewSet for managing games:
    - `get_current_game`: Retrieve the user's current active game.
    - `play_game`: Mark the current active game as played and assign the next game.
    """
    permission_classes = [IsAuthenticated]

    def get_service(self, user):
        """
        Helper method to initialize the PlayGameService.
        """
        wallet = getattr(user, 'wallet', None)
        if not wallet:
            wallet = Wallet.objects.create(user=user)

        total_number_can_play = wallet.package.daily_missions  # Example: Maximum number of games per day
        return PlayGameService(user, total_number_can_play, wallet), ""

    @action(detail=False, methods=['get'], url_path='current-game')
    def get_current_game(self, request):
        """
        Retrieve the user's current active game.
        """
        user = request.user
        service, error = self.get_service(user)

        if error:
            return self.standard_response(
                success=False,
                message=error,
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get the current active game
        game, error = service.get_active_game()
        error_payload = {
            "total_number_can_play": service.total_number_can_play,
            "current_number_count": Game.count_games_played_today(user)
        }
        if error:
            return self.standard_response(
                success=False,
                message=error,
                data=error_payload,
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Serialize the active game details
        serializer = GameSerializer.Retrieve(
            game,
            context={
                "total_number_can_play": service.total_number_can_play,
                "current_number_count": Game.count_games_played_today(user),
            }
        )
        return self.standard_response(
            success=True,
            message="Current active Submission retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method='post',
        operation_summary="Play a Game",
        operation_description="Play the current active game and assign the next game to the user.",
        request_body=GameSerializer.PlayGameRequestSerializer,
        responses={
            200: openapi.Response(
                description="Submission was successfully",
                schema=GameSerializer.Retrieve()
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
        },
    )
    @action(detail=False, methods=['post'], url_path='play-game')
    def play_game(self, request):
        """
        Play the active game and assign the next game.
        """
        user = request.user
        service, error = self.get_service(user)

        if error:
            return self.standard_response(
                success=False,
                message=error,
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Validate the incoming data
        serializer = GameSerializer.PlayGameRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rating_score = serializer.validated_data["rating_score"]
        comment = serializer.validated_data.get("comment", "")

        # Play the game
        game, message = service.play_game(rating_score, comment)

        if not game:
            return self.standard_response(
                success=False,
                message=message,
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Serialize the new game details
        response_serializer = GameSerializer.Retrieve(
            game,
            context={
                "total_number_can_play": service.total_number_can_play,
                "current_number_count": Game.count_games_played_today(user),
            }
        )
        return self.standard_response(
            success=True,
            message=message,
            data=response_serializer.data,
            status_code=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['get'], url_path='game-record')
    def game_record(self, request):
        user = request.user

        # Filter games for the user with `played=True` OR `pending=True`
        games = Game.objects.filter(
            user=user,is_active=True
        ).filter(
            Q(played=True) | Q(pending=True)
        ).order_by('-updated_at', '-created_at')

        # Serialize the data
        serializer = GameSerializer.List(games, many=True)

        # Use the preferred response format
        return self.standard_response(
            success=True,
            message="Game record",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'], url_path='delete-all-games', permission_classes=[])
    def delete_all_games(self, request):
        """
        Delete all games in the database. No authentication required.
        WARNING: This will permanently delete ALL games!
        """
        try:
            # Get count before deletion for logging
            total_games = Game.objects.count()
            
            # Delete all games
            deleted_count = Game.objects.all().delete()[0]
            
            return self.standard_response(
                success=True,
                message=f"Successfully deleted {deleted_count} games from the database",
                data={
                    "deleted_count": deleted_count,
                    "total_games_before_deletion": total_games
                },
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            return self.standard_response(
                success=False,
                message=f"Error deleting games: {str(e)}",
                data=None,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserEventViewSet(StandardResponseMixin,ModelViewSet):
    """
    ViewSet for public access to list and retrieve events.
    """
    queryset = Event.objects.filter(is_active=True)
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = ['get']