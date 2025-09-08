from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.db.models import JSONField

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


class VegetationIndexSet(models.Model):
    """
    Stores a multiband GeoTIFF with multiple vegetation indices
    for a given land and acquisition date.
    Example: Band1=NDVI, Band2=NDRE, Band3=NDMI
    """
    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name="veg_index_sets", verbose_name="Land")
    acquisition_date = models.DateField(verbose_name="Acquisition Date")
    file_path = models.CharField(max_length=500, verbose_name="Multiband GeoTIFF Path")
    stats = JSONField(default=dict, verbose_name="Index Stats")
    # Example stats structure:
    # {
    #   "NDVI": {"min": -0.2, "max": 0.9, "mean": 0.55},
    #   "NDRE": {"min": -0.1, "max": 0.8, "mean": 0.45},
    #   "NDMI": {"min": -0.3, "max": 0.7, "mean": 0.30}
    # }

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Vegetation Index Set"
        verbose_name_plural = "Vegetation Index Sets"
        ordering = ["-acquisition_date"]
        constraints = [
            models.UniqueConstraint(fields=["land", "acquisition_date"], name="uniq_land_indexset_date"),
        ]

    def __str__(self):
        return f"{self.land.name} | Indices | {self.acquisition_date}"
