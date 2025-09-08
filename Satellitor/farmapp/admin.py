from django.contrib import admin
try:
    from django.contrib.gis.admin import OSMGeoAdmin as BaseGeoAdmin
except Exception:
    from django.contrib import admin as _admin
    BaseGeoAdmin = _admin.ModelAdmin

from .models import (
    Land,
    LandSize,
    Crops,
    CropInstances,
    VegetationIndexSet,
)


@admin.register(Land)
class LandAdmin(BaseGeoAdmin):
    list_display = ("name", "user", "status", "created_date", "last_updated")
    list_filter = ("status", "user")
    search_fields = ("name", "user__username", "location", "soil_type")
    default_zoom = 12
    default_lon = 0
    default_lat = 0


@admin.register(LandSize)
class LandSizeAdmin(admin.ModelAdmin):
    list_display = ("land", "value", "unit")
    list_filter = ("unit",)
    search_fields = ("land__name",)


@admin.register(Crops)
class CropsAdmin(admin.ModelAdmin):
    list_display = ("crop_name",)
    search_fields = ("crop_name",)


@admin.register(CropInstances)
class CropInstancesAdmin(admin.ModelAdmin):
    list_display = ("crop", "land", "planting_date", "harvest_date", "season")
    list_filter = ("season", "crop")
    search_fields = ("land__name", "crop__crop_name")



@admin.register(VegetationIndexSet)
class VegetationIndexSetAdmin(admin.ModelAdmin):
    list_display = ("land", "acquisition_date", "file_path")
    list_filter = ("acquisition_date",)
    search_fields = ("land__name", "file_path")
