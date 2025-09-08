from typing import Any

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from rest_framework import serializers

from .models import (
    Land,
    LandSize,
    Crops,
    CropInstances,
    VegetationIndexSet,
)


class GeometryMixin:
    def to_representation_geometry(self, geometry) -> Any:
        if geometry is None:
            return None
        # Return GeoJSON representation
        return GEOSGeometry(geometry.wkt, srid=geometry.srid).geojson

    def parse_geometry(self, value) -> GEOSGeometry:
        if value is None:
            return None
        try:
            if isinstance(value, (dict, list,)):
                # GeoJSON dict
                geom = GEOSGeometry(str(value).replace("'", '"'))
            elif isinstance(value, str):
                # Can be GeoJSON string or WKT
                geom = GEOSGeometry(value)
            else:
                raise serializers.ValidationError("Unsupported geometry format")
        except GEOSException as exc:
            raise serializers.ValidationError(f"Invalid geometry: {exc}")
        if geom.srid is None:
            geom.srid = 4326
        return geom


class LandSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandSize
        fields = ["id", "land", "value", "unit"]
        read_only_fields = ["id"]


class LandSerializer(serializers.ModelSerializer, GeometryMixin):
    boundary = serializers.SerializerMethodField()

    class Meta:
        model = Land
        fields = [
            "id",
            "name",
            "created_date",
            "last_updated",
            "user",
            "location",
            "soil_type",
            "irrigation_type",
            "status",
            "notes",
            "image_url",
            "boundary",
        ]
        read_only_fields = ["id", "created_date", "last_updated", "user"]

    def get_boundary(self, obj: Land) -> Any:
        return self.to_representation_geometry(obj.boundary)

    def validate(self, attrs):
        # Accept incoming geometry from context data if present
        request = self.context.get("request")
        if request and request.method in ["POST", "PUT", "PATCH"]:
            incoming = request.data.get("boundary")
            if incoming is not None:
                attrs["boundary"] = self.parse_geometry(incoming)
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user
        return super().create(validated_data)


class CropsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crops
        fields = ["id", "crop_name", "description"]
        read_only_fields = ["id"]


class CropInstancesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropInstances
        fields = [
            "id",
            "land",
            "crop",
            "planting_date",
            "harvest_date",
            "season",
        ]
        read_only_fields = ["id"]




class VegetationIndexSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = VegetationIndexSet
        fields = [
            "id",
            "land",
            "acquisition_date",
            "file_path",
            "stats",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


