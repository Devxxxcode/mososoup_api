from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsSiteAdmin
from rest_framework.decorators import action
from rest_framework import status
from .models import Pack
from .serializers import PackSerializer
from shared.mixins import StandardResponseMixin
from rest_framework.response import Response
from shared.helpers import create_admin_log
from shared.cache_utils import (
    cache_result, invalidate_package_cache, 
    get_packages_cache_key
)


class PackViewSet(StandardResponseMixin, ModelViewSet):
    """
    ViewSet for managing Packs.
    """
    queryset = Pack.objects.all()
    serializer_class = PackSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @cache_result('PACKAGES', 'all')  # Literal string "all"
    def list(self, request, *args, **kwargs):
        """List all packages with caching"""
        return super().list(request, *args, **kwargs)

    @cache_result('PACKAGES', ['pk'])  # Cache by pack ID (pk in kwargs)
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific package with caching"""
        return super().retrieve(request, *args, **kwargs)

    def get_serializer_context(self):
        # Add request to the serializer context
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        """
        Custom permission logic for different actions.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only admins can create, update, or delete packs
            return [IsSiteAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        pack = serializer.save()
        # Invalidate package cache after creation
        invalidate_package_cache()
        try:
            create_admin_log(self.request, f"Created pack '{pack.name}' (USD {pack.usd_value})")
        except Exception:
            pass

    def perform_update(self, serializer):
        pack = serializer.save()
        # Invalidate package cache after update
        invalidate_package_cache()
        try:
            state = "active" if pack.is_active else "inactive"
            create_admin_log(self.request, f"Updated pack '{pack.name}' (USD {pack.usd_value}), now {state}")
        except Exception:
            pass

    def perform_destroy(self, instance):
        name = instance.name
        usd = instance.usd_value
        super().perform_destroy(instance)
        # Invalidate package cache after deletion
        invalidate_package_cache()
        try:
            create_admin_log(self.request, f"Deleted pack '{name}' (USD {usd})")
        except Exception:
            pass

    @cache_result('PACKAGES', 'active')  # Literal string "active"
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def active_packs(self, request):
        """
        Endpoint to get all active packs.
        """
        active_packs = self.queryset.filter(is_active=True).order_by('usd_value')
        serializer = self.get_serializer(active_packs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @cache_result('PACKAGES', 'inactive')  # Literal string "inactive"
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def inactive_packs(self, request):
        """
        Endpoint to get all inactive packs.
        """
        inactive_packs = self.queryset.filter(is_active=False).order_by('usd_value')
        serializer = self.get_serializer(inactive_packs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
