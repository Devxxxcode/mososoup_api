from rest_framework.routers import DefaultRouter
from .views import DepositViewSet,PaymentMethodViewSet,WithdrawalViewSet

router = DefaultRouter()
router.register(r'deposits', DepositViewSet, basename='deposit')
router.register(r'payments', PaymentMethodViewSet, basename='deposit')
router.register(r'withdrawals', WithdrawalViewSet, basename='withdrawal')

urlpatterns = router.urls
