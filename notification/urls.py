from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserNotificationViewSet,AdminNotificationViewSet,AdminLogReadView

router = DefaultRouter()
router.register(r'notifications', UserNotificationViewSet, basename='user-notification')
router.register(r'admin-notifications', AdminNotificationViewSet, basename='user-notification')
router.register(r'admin-logs', AdminLogReadView, basename='user-logs')

urlpatterns = [
    path('', include(router.urls)),
]