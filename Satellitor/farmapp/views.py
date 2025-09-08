from rest_framework import permissions, viewsets
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Value
from django.contrib.gis.db.models.functions import Area as DBArea
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


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an attribute named 'user'.
    """
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

    @transaction.atomic
    def perform_create(self, serializer):
        land = serializer.save()
        # Compute geodesic area (square meters) using database ST_Area on geography
        area_row = (
            Land.objects.filter(pk=land.pk)
            .annotate(area_m2=DBArea('boundary'))
            .values('area_m2')
            .first()
        )
        if not area_row:
            return
        # For geography=True, DBArea returns a django.contrib.gis.measure.Area object
        area_obj = area_row['area_m2']
        if area_obj is None:
            return
        # Safely extract square meters
        area_m2 = None
        if hasattr(area_obj, 'sq_m'):
            area_m2 = float(area_obj.sq_m)
        else:
            area_m2 = float(area_obj)
        if area_m2 is None:
            return
        # Unit conversions
        SQM_PER_HECTARE = 10000.0
        SQM_PER_ACRE = 4046.8564224
        SQM_PER_FEDDAN = 4200.0

        size_specs = [
            (area_m2, 'square_meter'),
            (area_m2 / SQM_PER_HECTARE, 'hectare'),
            (area_m2 / SQM_PER_ACRE, 'acre'),
            (area_m2 / SQM_PER_FEDDAN, 'feddan'),
        ]

        # Create or update LandSize entries
        for value, unit in size_specs:
            LandSize.objects.update_or_create(
                land=land,
                unit=unit,
                defaults={'value': round(value, 4)},
            )


class LandSizeViewSet(viewsets.ModelViewSet):
    queryset = LandSize.objects.all()
    serializer_class = LandSizeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LandSize.objects.filter(land__user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        # Return all sizes for the land of this LandSize id
        instance = self.get_object()
        queryset = LandSize.objects.filter(land=instance.land, land__user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # Update one size, synchronize others, and return all sizes for that land
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        queryset = LandSize.objects.filter(land=instance.land, land__user=request.user)
        out = self.get_serializer(queryset, many=True)
        return Response(out.data)

    @transaction.atomic
    def perform_update(self, serializer):
        landsize = serializer.save()
        land = landsize.land
        # Ensure ownership
        if land.user != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not allowed to modify this land's sizes")

        # Convert updated unit to square meters
        value = float(landsize.value)
        unit = landsize.unit
        SQM_PER = {
            'square_meter': 1.0,
            'hectare': 10000.0,
            'acre': 4046.8564224,
            'feddan': 4200.0,
        }
        sqm = value * SQM_PER[unit]

        # Recompute all units from sqm
        recomputed = [
            (sqm, 'square_meter'),
            (sqm / SQM_PER['hectare'], 'hectare'),
            (sqm / SQM_PER['acre'], 'acre'),
            (sqm / SQM_PER['feddan'], 'feddan'),
        ]
        for new_value, u in recomputed:
            LandSize.objects.update_or_create(
                land=land,
                unit=u,
                defaults={'value': round(new_value, 4)},
            )

    @transaction.atomic
    def perform_create(self, serializer):
        # If a manual land size is created, normalize all sizes based on it
        landsize = serializer.save()
        land = landsize.land
        if land.user != self.request.user and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not allowed to modify this land's sizes")

        value = float(landsize.value)
        unit = landsize.unit
        SQM_PER = {
            'square_meter': 1.0,
            'hectare': 10000.0,
            'acre': 4046.8564224,
            'feddan': 4200.0,
        }
        sqm = value * SQM_PER[unit]
        recomputed = [
            (sqm, 'square_meter'),
            (sqm / SQM_PER['hectare'], 'hectare'),
            (sqm / SQM_PER['acre'], 'acre'),
            (sqm / SQM_PER['feddan'], 'feddan'),
        ]
        for new_value, u in recomputed:
            LandSize.objects.update_or_create(
                land=land,
                unit=u,
                defaults={'value': round(new_value, 4)},
            )


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


