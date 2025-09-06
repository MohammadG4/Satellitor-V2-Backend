from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LandViewSet,
    LandSizeViewSet,
    CropsViewSet,
    CropInstancesViewSet,
    CropCalendarViewSet,
    SatelliteImageViewSet,
    VegetationIndexViewSet,
)

router = DefaultRouter()
router.register(r'lands', LandViewSet, basename='land')
router.register(r'land-sizes', LandSizeViewSet, basename='landsize')
router.register(r'crops', CropsViewSet, basename='crops')
router.register(r'crop-instances', CropInstancesViewSet, basename='cropinstances')
router.register(r'crop-calendar', CropCalendarViewSet, basename='cropcalendar')
router.register(r'satellite-images', SatelliteImageViewSet, basename='satelliteimage')
router.register(r'vegetation-indices', VegetationIndexViewSet, basename='vegetationindex')

urlpatterns = [
    path('', include(router.urls)),
]
