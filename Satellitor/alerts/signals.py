from django.db.models.signals import post_save
from django.dispatch import receiver
from farmapp.models import Land
from .models import AlertScenario


@receiver(post_save, sender=Land)
def create_default_scenarios(sender, instance, created, **kwargs):
    """Automatically create all default scenarios when a new Land is created"""
    if created:
        # Define all default scenarios with their parameters
        default_scenarios = [
            {
                'name': 'Rapid NDVI Drop',
                'description': 'Detects sudden drops in NDVI indicating acute stress',
                'scenario_type': 'rapid_ndvi_drop',
                'is_active': True,
                'parameters': {
                    'drop_threshold_percent': 15.0,
                    'lookback_observations': 2,
                    'min_ndvi_value': 0.1
                }
            },
            {
                'name': 'Spatial Anomaly Detection',
                'description': 'Detects localized problems using grid-based analysis',
                'scenario_type': 'spatial_anomaly',
                'is_active': True,
                'parameters': {
                    'grid_size_meters': 10,
                    'anomaly_threshold_percent': 15.0,
                    'area_threshold_percent': 20.0,
                    'min_ndvi_value': 0.1
                }
            },
            {
                'name': 'Growth Stagnation',
                'description': 'Detects when expected growth is not happening',
                'scenario_type': 'growth_stagnation',
                'is_active': True,
                'parameters': {
                    'min_slope_threshold': 0.01,
                    'stagnation_days': 10,
                    'min_observations': 3
                }
            },
            {
                'name': 'Below Historical Percentile',
                'description': 'Detects unusually low NDVI compared to historical data',
                'scenario_type': 'below_historical_percentile',
                'is_active': True,
                'parameters': {
                    'percentile_threshold': 10.0,
                    'historical_years': 3,
                    'min_observations': 5
                }
            },
            {
                'name': 'Phenology Delay',
                'description': 'Detects delays in season start or progression',
                'scenario_type': 'phenology_delay',
                'is_active': True,
                'parameters': {
                    'delay_threshold_days': 14,
                    'sos_threshold': 0.3,
                    'min_observations': 5
                }
            },
            {
                'name': 'Poor Emergence',
                'description': 'Detects persistent low NDVI after sowing',
                'scenario_type': 'poor_emergence',
                'is_active': True,
                'parameters': {
                    'emergence_threshold': 0.2,
                    'days_after_sowing': 21,
                    'min_ndvi_value': 0.1
                }
            },
            {
                'name': 'Long-term Trend Decline',
                'description': 'Detects multi-year declining baseline',
                'scenario_type': 'long_term_trend_decline',
                'is_active': True,
                'parameters': {
                    'trend_threshold': -0.01,
                    'min_observations': 10,
                    'analysis_period_days': 365
                }
            }
        ]
        
        # Create scenarios for this land
        for scenario_data in default_scenarios:
            AlertScenario.objects.create(
                land=instance,
                user=instance.user,
                name=scenario_data['name'],
                description=scenario_data['description'],
                scenario_type=scenario_data['scenario_type'],
                is_active=scenario_data['is_active'],
                parameters=scenario_data['parameters']
            )
