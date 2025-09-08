from rest_framework import permissions, viewsets
from rest_framework_gis.filters import InBBoxFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    Land,
    LandSize,
    Crops,
    CropInstances,
    VegetationIndexSet,
)
from .serializers import (
    LandSerializer,
    LandSizeSerializer,
    CropsSerializer,
    CropInstancesSerializer,
    VegetationIndexSetSerializer,
)

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to authenticated users.
    Only staff/admin users can add, update, or delete.
    """
    def has_permission(self, request, view):
        # Everyone who is authenticated can read
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Only staff/admin can modify
        return request.user and request.user.is_staff



class LandViewSet(viewsets.ModelViewSet):
    queryset = Land.objects.all()
    serializer_class = LandSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [InBBoxFilter]
    bbox_filter_field = 'boundary'
    bbox_filter_include_overlapping = True

    def get_queryset(self):
        return Land.objects.filter(user=self.request.user)


class LandSizeViewSet(viewsets.ModelViewSet):
    queryset = LandSize.objects.all()
    serializer_class = LandSizeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LandSize.objects.filter(land__user=self.request.user)


class CropsViewSet(viewsets.ModelViewSet):
    queryset = Crops.objects.all()
    serializer_class = CropsSerializer
    permission_classes = [IsAdminOrReadOnly]


class CropInstancesViewSet(viewsets.ModelViewSet):
    queryset = CropInstances.objects.all()
    serializer_class = CropInstancesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CropInstances.objects.filter(land__user=self.request.user)




class VegetationIndexSetViewSet(viewsets.ModelViewSet):
    queryset = VegetationIndexSet.objects.all()
    serializer_class = VegetationIndexSetSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['land', 'acquisition_date']
    search_fields = ['land__name']
    ordering_fields = ['acquisition_date', 'created_at']
    ordering = ['-acquisition_date']

    def get_queryset(self):
        # Only return vegetation index sets for the user's lands
        return VegetationIndexSet.objects.filter(land__user=self.request.user)

