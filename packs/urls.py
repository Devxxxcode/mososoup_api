from rest_framework.routers import DefaultRouter
from .views import PackViewSet

# Initialize the router
router = DefaultRouter()
router.register(r'packs', PackViewSet, basename='packs')

# URL patterns
urlpatterns = router.urls
