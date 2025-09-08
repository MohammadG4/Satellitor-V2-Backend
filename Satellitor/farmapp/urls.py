from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LandViewSet,
    LandSizeViewSet,
    CropsViewSet,
    CropInstancesViewSet,
    VegetationIndexSetViewSet,
)

router = DefaultRouter()
router.register(r'lands', LandViewSet, basename='land')
router.register(r'land-sizes', LandSizeViewSet, basename='landsize')
router.register(r'crops', CropsViewSet, basename='crops')
router.register(r'crop-instances', CropInstancesViewSet, basename='cropinstances')
router.register(r'vegetation-index-sets', VegetationIndexSetViewSet, basename='vegetationindexset')

urlpatterns = [
    path('', include(router.urls)),
]
