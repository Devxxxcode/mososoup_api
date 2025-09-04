from django.contrib import admin
from django.urls import path,include,re_path
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Mososoup API",
        default_version='v1',
        description="API documentation for Mososoup",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class HelloWorldView(APIView):
    """
    A simple API view to return 'Hello, World!'.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({"message": "Hello, World!"})

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation - only available in DEBUG mode
    path('hello-world/', HelloWorldView.as_view(), name='hello-world'),
    
    path('site_admin/',include("administration.urls")),
    path('site_admin/',include("users.admin_urls")),
    path('auth/',include("users.urls")),
    path('api/', include('packs.urls')),
    path('api/', include('finances.urls')),
    path("api/",include("game.urls")),
    path("api/",include("notification.urls")),
]

# Add Swagger and Redoc documentation URLs only when DEBUG is True
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
