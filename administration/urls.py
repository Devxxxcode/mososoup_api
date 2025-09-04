from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import SettingsViewSet,AdminDepositViewSet,EventViewSet,AdminUserManagementViewSet,OnHoldViewSet,AdminNegativeUserManagementViewSet,AdminWithdrawalViewSet

router = DefaultRouter()
router.register(r'settings', SettingsViewSet, basename='settings')


router.register(r'deposits', AdminDepositViewSet, basename='admin-deposit')
router.register(r'withdrawals', AdminWithdrawalViewSet, basename='admin-withdrawal'),
router.register(r'events', EventViewSet, basename='event')
router.register(r'users', AdminUserManagementViewSet, basename='users')
router.register(r'onholds', OnHoldViewSet, basename='onhold')
router.register(r'negative-users', AdminNegativeUserManagementViewSet, basename='negative-users')


urlpatterns = [
    path('', include(router.urls)),
]
