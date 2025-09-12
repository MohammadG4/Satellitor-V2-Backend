from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertRuleViewSet, AlertViewSet, NotificationLogViewSet

router = DefaultRouter()
router.register(r'alert-rules', AlertRuleViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'notification-logs', NotificationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
