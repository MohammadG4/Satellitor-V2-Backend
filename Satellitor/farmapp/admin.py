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
    CropCalendar,
    SatelliteImage,
    VegetationIndex,
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


@admin.register(CropCalendar)
class CropCalendarAdmin(admin.ModelAdmin):
    list_display = ("crop", "season_name", "start_month", "end_month")
    list_filter = ("season_name",)
    search_fields = ("crop__crop_name",)


@admin.register(SatelliteImage)
class SatelliteImageAdmin(admin.ModelAdmin):
    list_display = ("land", "band_name", "acquisition_date", "resolution_m")
    list_filter = ("band_name", "acquisition_date")
    search_fields = ("land__name", "band_name", "file_path")


@admin.register(VegetationIndex)
class VegetationIndexAdmin(admin.ModelAdmin):
    list_display = ("land", "index_type", "acquisition_date", "min_value", "mean_value", "max_value")
    list_filter = ("index_type", "acquisition_date")
    search_fields = ("land__name", "index_type", "value_raster_path")
