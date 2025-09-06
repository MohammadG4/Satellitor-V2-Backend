from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Land(models.Model):
    """Model representing a piece of land/farm with geospatial boundary"""
    name = models.CharField(max_length=100, verbose_name="Land Name")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Created Date")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Last Updated")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lands", verbose_name="Owner")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Location")
    soil_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Soil Type")
    irrigation_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Irrigation Type")
    status = models.BooleanField(default=True, verbose_name="Active Status")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    image_url = models.URLField(blank=True, null=True, verbose_name="Image URL")
    # Geospatial polygon representing the land boundary (WGS84)
    boundary = models.PolygonField(srid=4326, geography=True, spatial_index=True, verbose_name="Boundary")

    class Meta:
        verbose_name = "Land"
        verbose_name_plural = "Lands"
        ordering = ['-created_date']
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uniq_user_land_name"),
        ]

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class SatelliteImage(models.Model):
    """Metadata for downloaded satellite band rasters associated with a land."""
    BAND_CHOICES = [
        ("B01", "Band 1 - Coastal Aerosol"),
        ("B02", "Band 2 - Blue"),
        ("B03", "Band 3 - Green"),
        ("B04", "Band 4 - Red"),
        ("B05", "Band 5 - Red Edge 1"),
        ("B06", "Band 6 - Red Edge 2"),
        ("B07", "Band 7 - Red Edge 3"),
        ("B08", "Band 8 - NIR"),
        ("B8A", "Band 8A - Narrow NIR"),
        ("B09", "Band 9 - Water Vapour"),
        ("B11", "Band 11 - SWIR 1"),
        ("B12", "Band 12 - SWIR 2"),
    ]

    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name="satellite_images", verbose_name="Land")
    band_name = models.CharField(max_length=4, choices=BAND_CHOICES, verbose_name="Band Name")
    acquisition_date = models.DateField(verbose_name="Acquisition Date")
    file_path = models.CharField(max_length=500, verbose_name="GeoTIFF File Path")
    resolution_m = models.PositiveIntegerField(verbose_name="Resolution (m)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Satellite Image"
        verbose_name_plural = "Satellite Images"
        ordering = ["-acquisition_date", "band_name"]
        constraints = [
            models.UniqueConstraint(fields=["land", "band_name", "acquisition_date"], name="uniq_land_band_date"),
        ]

    def __str__(self):
        return f"{self.land.name} | {self.band_name} | {self.acquisition_date}"


class LandSize(models.Model):
    """Model representing land size measurements"""
    UNIT_CHOICES = [
        ('feddan', 'Feddan'),
        ('acre', 'Acre'),
        ('hectare', 'Hectare'),
        ('square_meter', 'Square Meter'),
    ]
    
    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name='sizes')
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Size Value")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='feddan', verbose_name="Unit")

    class Meta:
        verbose_name = "Land Size"
        verbose_name_plural = "Land Sizes"

    def __str__(self):
        return f"{self.land.name} - {self.value} {self.unit}"


class Crops(models.Model):
    """Model representing reference crops"""
    crop_name = models.CharField(max_length=100, unique=True, verbose_name="Crop Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    class Meta:
        verbose_name = "Crop"
        verbose_name_plural = "Crops"
        ordering = ['crop_name']

    def __str__(self):
        return self.crop_name


class CropInstances(models.Model):
    """Model representing actual crop plantings on land"""
    SEASON_CHOICES = [
        ('Winter', 'شتوي'),
        ('Summer', 'صيفي'),
        ('Nile', 'نيل'),
        ('Spring', 'ربيعي'),
        ('Autumn', 'خريفي'),
    ]
    
    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name='crop_instances', verbose_name="Land")
    crop = models.ForeignKey(Crops, on_delete=models.CASCADE, related_name='instances', verbose_name="Crop")
    planting_date = models.DateField(verbose_name="Planting Date")
    harvest_date = models.DateField(blank=True, null=True, verbose_name="Harvest Date")
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, blank=True, null=True, verbose_name="Season")

    class Meta:
        verbose_name = "Crop Instance"
        verbose_name_plural = "Crop Instances"
        ordering = ['-planting_date']
        constraints = [
            models.UniqueConstraint(fields=["land", "crop", "planting_date"], name="uniq_land_crop_planting"),
        ]

    def __str__(self):
        return f"{self.crop.crop_name} on {self.land.name} - {self.planting_date}"


class CropCalendar(models.Model):
    """Model representing when each crop should be planted"""
    crop = models.ForeignKey(Crops, on_delete=models.CASCADE, related_name='calendar', verbose_name="Crop")
    season_name = models.CharField(max_length=20, verbose_name="Season Name")
    start_month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Start Month"
    )
    end_month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="End Month"
    )

    class Meta:
        verbose_name = "Crop Calendar"
        verbose_name_plural = "Crop Calendars"
        ordering = ['crop', 'start_month']
        constraints = [
            models.CheckConstraint(check=models.Q(start_month__gte=1) & models.Q(start_month__lte=12), name="start_month_valid_range"),
            models.CheckConstraint(check=models.Q(end_month__gte=1) & models.Q(end_month__lte=12), name="end_month_valid_range"),
            models.CheckConstraint(check=models.Q(end_month__gte=models.F('start_month')), name="end_month_after_start_month"),
            models.UniqueConstraint(fields=["crop", "season_name"], name="uniq_crop_season_name"),
        ]

    def __str__(self):
        return f"{self.crop.crop_name} - {self.season_name} ({self.start_month}-{self.end_month})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_month > self.end_month:
            raise ValidationError("Start month cannot be greater than end month")


class VegetationIndex(models.Model):
    """Computed vegetation index rasters for a land, optionally derived from a satellite image."""
    INDEX_CHOICES = [
        ("NDVI", "NDVI - Normalized Difference Vegetation Index"),
        ("NDRE", "NDRE - Normalized Difference Red Edge"),
        ("NDMI", "NDMI - Normalized Difference Moisture Index"),
    ]

    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name="vegetation_indices", verbose_name="Land")
    source_image = models.ForeignKey(
        'SatelliteImage', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='indices', verbose_name="Source Satellite Image"
    )
    index_type = models.CharField(max_length=10, choices=INDEX_CHOICES, verbose_name="Index Type")
    acquisition_date = models.DateField(verbose_name="Acquisition Date")
    value_raster_path = models.CharField(max_length=500, verbose_name="Index GeoTIFF File Path")
    min_value = models.FloatField(null=True, blank=True, verbose_name="Min")
    max_value = models.FloatField(null=True, blank=True, verbose_name="Max")
    mean_value = models.FloatField(null=True, blank=True, verbose_name="Mean")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Vegetation Index"
        verbose_name_plural = "Vegetation Indices"
        ordering = ["-acquisition_date", "index_type"]
        constraints = [
            models.UniqueConstraint(fields=["land", "index_type", "acquisition_date"], name="uniq_land_index_date"),
        ]

    def __str__(self):
        return f"{self.land.name} | {self.index_type} | {self.acquisition_date}"
