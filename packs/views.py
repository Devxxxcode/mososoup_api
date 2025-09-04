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


class PackViewSet(StandardResponseMixin, ModelViewSet):
    """
    ViewSet for managing Packs.
    """
    queryset = Pack.objects.all()
    serializer_class = PackSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

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
        try:
            create_admin_log(self.request, f"Created pack '{pack.name}' (USD {pack.usd_value})")
        except Exception:
            pass

    def perform_update(self, serializer):
        pack = serializer.save()
        try:
            state = "active" if pack.is_active else "inactive"
            create_admin_log(self.request, f"Updated pack '{pack.name}' (USD {pack.usd_value}), now {state}")
        except Exception:
            pass

    def perform_destroy(self, instance):
        name = instance.name
        usd = instance.usd_value
        super().perform_destroy(instance)
        try:
            create_admin_log(self.request, f"Deleted pack '{name}' (USD {usd})")
        except Exception:
            pass

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def active_packs(self, request):
        """
        Endpoint to get all active packs.
        """
        active_packs = self.queryset.filter(is_active=True).order_by('usd_value')
        serializer = self.get_serializer(active_packs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def inactive_packs(self, request):
        """
        Endpoint to get all inactive packs.
        """
        inactive_packs = self.queryset.filter(is_active=False).order_by('usd_value')
        serializer = self.get_serializer(inactive_packs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
