from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet,GameViewSet,UserEventViewSet

# Create a router and register the ProductViewSet
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'games', GameViewSet, basename='game')  # Register GameViewSet
router.register(r'events', UserEventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),  # Include all routes registered with the router
    
]
