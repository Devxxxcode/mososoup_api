from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserAuthViewSet,InvitationCodeViewSet

# Create a router and register the UserAuthViewSet
router = DefaultRouter()
router.register(r'', UserAuthViewSet, basename='auth')
router.register(r'invitation-codes', InvitationCodeViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)), 
]
