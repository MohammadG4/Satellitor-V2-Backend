from rest_framework import permissions, viewsets
from rest_framework_gis.filters import InBBoxFilter

from .models import (
    Land,
    LandSize,
    Crops,
    CropInstances,
    CropCalendar,
    SatelliteImage,
    VegetationIndex,
)
from .serializers import (
    LandSerializer,
    LandSizeSerializer,
    CropsSerializer,
    CropInstancesSerializer,
    CropCalendarSerializer,
    SatelliteImageSerializer,
    VegetationIndexSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, 'user', None)
        return owner == request.user


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
    permission_classes = [permissions.IsAuthenticated]


class CropInstancesViewSet(viewsets.ModelViewSet):
    queryset = CropInstances.objects.all()
    serializer_class = CropInstancesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CropInstances.objects.filter(land__user=self.request.user)


class CropCalendarViewSet(viewsets.ModelViewSet):
    queryset = CropCalendar.objects.all()
    serializer_class = CropCalendarSerializer
    permission_classes = [permissions.IsAuthenticated]


class SatelliteImageViewSet(viewsets.ModelViewSet):
    queryset = SatelliteImage.objects.all()
    serializer_class = SatelliteImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SatelliteImage.objects.filter(land__user=self.request.user)


class VegetationIndexViewSet(viewsets.ModelViewSet):
    queryset = VegetationIndex.objects.all()
    serializer_class = VegetationIndexSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VegetationIndex.objects.filter(land__user=self.request.user)

