#!/usr/bin/env python3
"""
Test script for the Alert System
Run this to test the alert system functionality
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the Django project to the Python path
sys.path.append('Satellitor')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Satellitor.settings')
django.setup()

from django.contrib.auth import get_user_model
from farmapp.models import Land, VegetationIndexSet
from alerts.models import AlertRule, Alert, NotificationLog
from alerts.services import AlertManager

User = get_user_model()

def test_alert_system():
    """Test the alert system functionality"""
    print("🚨 Testing Alert System...")
    
    # Create test user
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={'first_name': 'Test', 'last_name': 'User'}
    )
    print(f"✅ User: {user.email} ({'created' if created else 'exists'})")
    
    # Create test land
    from django.contrib.gis.geos import Polygon
    test_polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
    
    land, created = Land.objects.get_or_create(
        name='Test Field',
        user=user,
        defaults={
            'boundary': test_polygon,
            'status': True
        }
    )
    print(f"✅ Land: {land.name} ({'created' if created else 'exists'})")
    
    # Create test vegetation index set
    test_stats = {
        'NDVI': {'min': 0.1, 'max': 0.8, 'mean': 0.25, 'std': 0.1, 'count': 1000},
        'NDRE': {'min': 0.05, 'max': 0.7, 'mean': 0.2, 'std': 0.08, 'count': 1000},
        'EVI': {'min': 0.0, 'max': 0.9, 'mean': 0.3, 'std': 0.12, 'count': 1000},
        'SAVI': {'min': 0.0, 'max': 0.85, 'mean': 0.28, 'std': 0.11, 'count': 1000},
        'GCI': {'min': 0.0, 'max': 0.75, 'mean': 0.22, 'std': 0.09, 'count': 1000}
    }
    
    veg_set, created = VegetationIndexSet.objects.get_or_create(
        land=land,
        acquisition_date=datetime.now().date(),
        defaults={
            'file_path': 'test/path.tiff',
            'stats': test_stats
        }
    )
    print(f"✅ Vegetation Index Set: {veg_set.acquisition_date} ({'created' if created else 'exists'})")
    
    # Create test alert rule
    alert_rule, created = AlertRule.objects.get_or_create(
        name='Test Low NDVI Alert',
        land=land,
        user=user,
        defaults={
            'description': 'Test alert when NDVI drops below 0.3',
            'alert_type': 'threshold',
            'severity': 'medium',
            'index_name': 'NDVI',
            'threshold_value': 0.3,
            'comparison_operator': 'lt',
            'is_active': True,
            'notification_methods': ['email'],
            'cooldown_hours': 1
        }
    )
    print(f"✅ Alert Rule: {alert_rule.name} ({'created' if created else 'exists'})")
    
    # Test alert processing
    print("\n🔍 Testing Alert Processing...")
    alert_manager = AlertManager()
    
    # Process alerts for the vegetation index set
    alert_manager.process_new_vegetation_data(land, veg_set)
    
    # Check if alert was created
    alerts = Alert.objects.filter(land=land)
    print(f"✅ Alerts created: {alerts.count()}")
    
    for alert in alerts:
        print(f"   - Alert {alert.id}: {alert.message}")
        print(f"     Status: {alert.status}, Severity: {alert.severity}")
        print(f"     Index: {alert.index_name} = {alert.index_value} (threshold: {alert.threshold_value})")
    
    # Test alert rule
    print("\n🧪 Testing Alert Rule...")
    index_value = alert_manager.processor.get_index_value(veg_set, 'NDVI')
    should_trigger = alert_manager.processor.should_trigger_alert(alert_rule, index_value)
    
    print(f"   NDVI Value: {index_value}")
    print(f"   Threshold: {alert_rule.threshold_value}")
    print(f"   Should Trigger: {should_trigger}")
    
    # Test alert status changes
    if alerts.exists():
        alert = alerts.first()
        print(f"\n📝 Testing Alert Status Changes...")
        
        # Acknowledge
        if alert_manager.acknowledge_alert(alert.id, user):
            print("   ✅ Alert acknowledged")
        
        # Resolve
        if alert_manager.resolve_alert(alert.id, user):
            print("   ✅ Alert resolved")
    
    # Test notification logs
    notification_logs = NotificationLog.objects.filter(alert__land=land)
    print(f"\n📧 Notification Logs: {notification_logs.count()}")
    
    for log in notification_logs:
        print(f"   - {log.notification_type}: {log.status} to {log.recipient}")
    
    print("\n🎉 Alert System Test Completed!")
    print(f"   - User: {user.email}")
    print(f"   - Land: {land.name}")
    print(f"   - Alert Rules: {AlertRule.objects.filter(user=user).count()}")
    print(f"   - Alerts: {Alert.objects.filter(user=user).count()}")
    print(f"   - Notification Logs: {NotificationLog.objects.filter(alert__user=user).count()}")

if __name__ == '__main__':
    test_alert_system()
