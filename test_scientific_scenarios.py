#!/usr/bin/env python3
"""
Test script for Scientific Alert Scenarios
Demonstrates advanced agricultural monitoring capabilities
"""

import os
import sys
import django
from datetime import datetime, timedelta
import numpy as np

# Add the Django project to the Python path
sys.path.append('Satellitor')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Satellitor.settings')
django.setup()

from django.contrib.auth import get_user_model
from farmapp.models import Land, VegetationIndexSet
from alerts.models import AlertScenario, Alert, NotificationLog
from alerts.alert_scenarios import AdvancedAlertProcessor

User = get_user_model()

def test_scientific_scenarios():
    """Test the scientific alert scenarios"""
    print("🌱 Testing Scientific Alert Scenarios...")
    
    # Get test data
    user = User.objects.filter(email='test@example.com').first()
    if not user:
        print("❌ Test user not found. Please run the basic alert test first.")
        return
    
    land = Land.objects.filter(user=user).first()
    if not land:
        print("❌ Test land not found. Please run the basic alert test first.")
        return
    
    print(f"✅ Using land: {land.name} (ID: {land.id})")
    
    # Get alert scenarios for this land
    scenarios = AlertScenario.objects.filter(land=land)
    print(f"✅ Found {scenarios.count()} alert scenarios")
    
    # Create test vegetation data with different patterns
    test_data = create_test_vegetation_data(land)
    
    # Test each scenario
    processor = AdvancedAlertProcessor()
    
    for scenario in scenarios:
        print(f"\n🔍 Testing scenario: {scenario.name}")
        print(f"   Type: {scenario.get_scenario_type_display()}")
        print(f"   Severity: {scenario.severity}")
        
        try:
            result = processor.process_scenario(scenario, test_data)
            
            if result.get('triggered', False):
                print(f"   🚨 ALERT TRIGGERED: {result.get('message', 'No message')}")
                print(f"   📊 Details: {result}")
            else:
                print(f"   ✅ No alert: {result.get('message', 'No message')}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n📈 Summary:")
    print(f"   - Total scenarios tested: {scenarios.count()}")
    print(f"   - Test data points: {len(test_data)}")
    print(f"   - Scenarios by type:")
    
    for scenario_type, _ in AlertScenario.SCENARIO_TYPES:
        count = scenarios.filter(scenario_type=scenario_type).count()
        if count > 0:
            print(f"     * {scenario_type}: {count}")

def create_test_vegetation_data(land):
    """Create test vegetation data with different patterns"""
    test_data = []
    base_date = datetime.now().date() - timedelta(days=30)
    
    # Create data with different patterns
    patterns = [
        # Normal growth pattern
        {'days': 0, 'ndvi': 0.2, 'ndre': 0.15, 'evi': 0.25, 'savi': 0.22, 'gci': 0.18},
        {'days': 5, 'ndvi': 0.3, 'ndre': 0.25, 'evi': 0.35, 'savi': 0.32, 'gci': 0.28},
        {'days': 10, 'ndvi': 0.4, 'ndre': 0.35, 'evi': 0.45, 'savi': 0.42, 'gci': 0.38},
        {'days': 15, 'ndvi': 0.5, 'ndre': 0.45, 'evi': 0.55, 'savi': 0.52, 'gci': 0.48},
        {'days': 20, 'ndvi': 0.6, 'ndre': 0.55, 'evi': 0.65, 'savi': 0.62, 'gci': 0.58},
        {'days': 25, 'ndvi': 0.7, 'ndre': 0.65, 'evi': 0.75, 'savi': 0.72, 'gci': 0.68},
        {'days': 30, 'ndvi': 0.8, 'ndre': 0.75, 'evi': 0.85, 'savi': 0.82, 'gci': 0.78},
    ]
    
    for pattern in patterns:
        date = base_date + timedelta(days=pattern['days'])
        
        # Create vegetation index set
        veg_set, created = VegetationIndexSet.objects.get_or_create(
            land=land,
            acquisition_date=date,
            defaults={
                'file_path': f'test/indices_{date}.tiff',
                'stats': {
                    'NDVI': {
                        'min': pattern['ndvi'] - 0.1,
                        'max': pattern['ndvi'] + 0.1,
                        'mean': pattern['ndvi'],
                        'std': 0.05,
                        'count': 1000
                    },
                    'NDRE': {
                        'min': pattern['ndre'] - 0.1,
                        'max': pattern['ndre'] + 0.1,
                        'mean': pattern['ndre'],
                        'std': 0.05,
                        'count': 1000
                    },
                    'EVI': {
                        'min': pattern['evi'] - 0.1,
                        'max': pattern['evi'] + 0.1,
                        'mean': pattern['evi'],
                        'std': 0.05,
                        'count': 1000
                    },
                    'SAVI': {
                        'min': pattern['savi'] - 0.1,
                        'max': pattern['savi'] + 0.1,
                        'mean': pattern['savi'],
                        'std': 0.05,
                        'count': 1000
                    },
                    'GCI': {
                        'min': pattern['gci'] - 0.1,
                        'max': pattern['gci'] + 0.1,
                        'mean': pattern['gci'],
                        'std': 0.05,
                        'count': 1000
                    }
                }
            }
        )
        
        test_data.append(veg_set)
    
    print(f"✅ Created {len(test_data)} test vegetation data points")
    return test_data

def demonstrate_scenario_types():
    """Demonstrate different scenario types with examples"""
    print("\n🔬 Scientific Alert Scenario Types:")
    
    scenarios = [
        {
            'name': 'Rapid NDVI Drop',
            'description': 'Detects sudden stress (>15% drop)',
            'use_case': 'Water stress, disease, damage detection',
            'frequency': 'Every 12 hours',
            'severity': 'High'
        },
        {
            'name': 'Spatial Anomaly',
            'description': 'Detects patchy problems in field',
            'use_case': 'Localized disease, nutrient deficiency',
            'frequency': 'Every 24 hours',
            'severity': 'Medium'
        },
        {
            'name': 'Growth Stagnation',
            'description': 'Detects lack of expected growth',
            'use_case': 'Emergence failure, nutrient limitation',
            'frequency': 'Every 48 hours',
            'severity': 'Medium'
        },
        {
            'name': 'Below Historical Percentile',
            'description': 'Detects drought conditions',
            'use_case': 'Drought early warning system',
            'frequency': 'Every 24 hours',
            'severity': 'Critical'
        },
        {
            'name': 'Phenology Delay',
            'description': 'Detects timing anomalies',
            'use_case': 'Planting problems, late emergence',
            'frequency': 'Every 72 hours',
            'severity': 'Medium'
        },
        {
            'name': 'Poor Emergence',
            'description': 'Monitors post-sowing success',
            'use_case': 'Crop establishment monitoring',
            'frequency': 'Every 24 hours',
            'severity': 'High'
        },
        {
            'name': 'Long-term Trend Decline',
            'description': 'Detects chronic degradation',
            'use_case': 'Soil health, environmental stress',
            'frequency': 'Weekly',
            'severity': 'Critical'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Use Case: {scenario['use_case']}")
        print(f"   Frequency: {scenario['frequency']}")
        print(f"   Severity: {scenario['severity']}")

if __name__ == '__main__':
    print("🌱 Scientific Alert Scenarios Test")
    print("=" * 50)
    
    demonstrate_scenario_types()
    
    print("\n" + "=" * 50)
    test_scientific_scenarios()
    
    print("\n🎉 Scientific Alert Scenarios Test Completed!")
    print("\n💡 Key Benefits:")
    print("   - Early detection of crop stress")
    print("   - Data-driven decision making")
    print("   - Proactive farm management")
    print("   - Scientific-based monitoring")
    print("   - Automated alert system")

