from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAuthViewSet

# Create a router and register the AdminAuthViewSet
router = DefaultRouter()
router.register(r'auth/admin', AdminAuthViewSet, basename='admin-auth')

# Include the router in the urlpatterns
urlpatterns = [
    path('', include(router.urls)),
]
