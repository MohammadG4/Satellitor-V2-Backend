from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from farmapp.models import Land
from alerts.models import AlertScenario
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with scientific alert scenarios for agricultural monitoring'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--land-id',
            type=int,
            help='Create scenarios for specific land ID only'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Create scenarios for specific user ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🌱 Populating Agricultural Alert Scenarios...')
        
        land_id = options.get('land_id')
        user_id = options.get('user_id')
        dry_run = options['dry_run']
        
        # Get lands to process
        if land_id:
            lands = Land.objects.filter(id=land_id)
        elif user_id:
            lands = Land.objects.filter(user_id=user_id)
        else:
            lands = Land.objects.all()
        
        if not lands.exists():
            self.stdout.write(self.style.ERROR('No lands found matching criteria'))
            return
        
        self.stdout.write(f'Found {lands.count()} lands to process')
        
        # Define scientific alert scenarios
        scenarios = self.get_scientific_scenarios()
        
        created_count = 0
        
        for land in lands:
            self.stdout.write(f'\nProcessing land: {land.name} (ID: {land.id})')
            
            for scenario_data in scenarios:
                if dry_run:
                    self.stdout.write(f'[DRY RUN] Would create: {scenario_data["name"]}')
                    continue
                
                # Check if scenario already exists
                if AlertScenario.objects.filter(land=land, name=scenario_data['name']).exists():
                    self.stdout.write(f'  ⚠️  Scenario already exists: {scenario_data["name"]}')
                    continue
                
                try:
                    # Create scenario
                    scenario = AlertScenario.objects.create(
                        name=scenario_data['name'],
                        description=scenario_data['description'],
                        scenario_type=scenario_data['scenario_type'],
                        land=land,
                        user=land.user,
                        parameters=scenario_data['parameters'],
                        severity=scenario_data['severity'],
                        is_active=scenario_data['is_active'],
                        cooldown_hours=scenario_data['cooldown_hours'],
                        notification_methods=scenario_data['notification_methods']
                    )
                    
                    self.stdout.write(f'  ✅ Created: {scenario.name}')
                    created_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Error creating {scenario_data["name"]}: {str(e)}')
                    )
        
        if dry_run:
            self.stdout.write(f'\n[DRY RUN] Would create {len(scenarios) * lands.count()} scenarios')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Successfully created {created_count} alert scenarios!')
            )
    
    def get_scientific_scenarios(self):
        """Get scientific alert scenarios based on agricultural research"""
        return [
            {
                'name': 'Rapid NDVI Drop - Acute Stress',
                'description': 'Detects sudden NDVI drops (>15% vs recent observations) indicating water stress, disease, damage, or harvesting. Critical for early intervention.',
                'scenario_type': 'rapid_ndvi_drop',
                'parameters': {
                    'drop_threshold': 15,  # Percentage drop threshold
                    'lookback_observations': 2,  # Compare to last 2 observations
                },
                'severity': 'high',
                'is_active': True,
                'cooldown_hours': 12,  # Check every 12 hours
                'notification_methods': ['email', 'sms']
            },
            {
                'name': 'Spatial Anomaly - Localized Problem',
                'description': 'Detects patchy problems where sub-areas show strong negative NDVI anomalies while rest of field is normal. Uses grid-based analysis.',
                'scenario_type': 'spatial_anomaly',
                'parameters': {
                    'cell_drop_threshold': 15,  # NDVI drop threshold per cell
                    'area_threshold': 20,  # Percentage of field area
                    'grid_size': 10,  # Grid cell size in meters
                },
                'severity': 'medium',
                'is_active': True,
                'cooldown_hours': 24,
                'notification_methods': ['email']
            },
            {
                'name': 'Growth Stagnation - Expected Rise Missing',
                'description': 'Detects when NDVI should be increasing during vegetative stage but remains flat or decreases. Indicates emergence failure or nutrient limitations.',
                'scenario_type': 'growth_stagnation',
                'parameters': {
                    'min_slope': 0.01,  # Minimum expected NDVI slope
                    'min_days': 10,  # Minimum days of stagnation
                    'lookback_days': 20,  # Days to analyze
                },
                'severity': 'medium',
                'is_active': True,
                'cooldown_hours': 48,
                'notification_methods': ['email']
            },
            {
                'name': 'Below Historical Percentile - Drought Warning',
                'description': 'Detects when current NDVI is unusually low compared to historical distribution for same calendar period. Robust drought early-warning system.',
                'scenario_type': 'below_historical',
                'parameters': {
                    'percentile_threshold': 10,  # Below 10th percentile
                    'historical_years': 3,  # Years of historical data
                },
                'severity': 'critical',
                'is_active': True,
                'cooldown_hours': 24,
                'notification_methods': ['email', 'sms', 'webhook']
            },
            {
                'name': 'Phenology Delay - SOS/EOS Deviation',
                'description': 'Detects delays in season start (SOS) or end (EOS) compared to historical expectations. Useful for planning and identifying planting problems.',
                'scenario_type': 'phenology_delay',
                'parameters': {
                    'delay_threshold': 14,  # Days delay threshold
                    'phase': 'SOS',  # Start of Season
                    'ndvi_threshold': 0.3,  # NDVI threshold for phase detection
                },
                'severity': 'medium',
                'is_active': True,
                'cooldown_hours': 72,
                'notification_methods': ['email']
            },
            {
                'name': 'Poor Emergence - Post-Sowing Monitoring',
                'description': 'Monitors NDVI after sowing to detect poor crop emergence. Alerts if NDVI remains below threshold for extended period after planting.',
                'scenario_type': 'poor_emergence',
                'parameters': {
                    'emergence_threshold': 0.2,  # NDVI threshold for emergence
                    'days_after_sowing': 14,  # Days to monitor after sowing
                    'sowing_date': None,  # Will be set per land
                },
                'severity': 'high',
                'is_active': False,  # Requires sowing date to be set
                'cooldown_hours': 24,
                'notification_methods': ['email', 'sms']
            },
            {
                'name': 'Long-term Trend Decline - Chronic Degradation',
                'description': 'Detects multi-year declining baseline in seasonal NDVI peaks. Indicates chronic soil degradation, nutrient depletion, or environmental stress.',
                'scenario_type': 'trend_decline',
                'parameters': {
                    'min_years': 2,  # Minimum years for trend analysis
                    'significance_level': 0.05,  # Statistical significance level
                },
                'severity': 'critical',
                'is_active': True,
                'cooldown_hours': 168,  # Weekly check
                'notification_methods': ['email', 'webhook']
            },
            # Additional specialized scenarios
            {
                'name': 'Early Season Stress - Post-Emergence',
                'description': 'Monitors for early season stress indicators in the first 30 days after emergence. Critical for crop establishment.',
                'scenario_type': 'rapid_ndvi_drop',
                'parameters': {
                    'drop_threshold': 10,  # Lower threshold for early season
                    'lookback_observations': 1,  # Compare to previous observation
                },
                'severity': 'high',
                'is_active': True,
                'cooldown_hours': 6,  # More frequent checks
                'notification_methods': ['email', 'sms']
            },
            {
                'name': 'Mid-Season Anomaly - Peak Growth',
                'description': 'Detects anomalies during peak growth period when NDVI should be at maximum. Indicates nutrient deficiency or pest damage.',
                'scenario_type': 'spatial_anomaly',
                'parameters': {
                    'cell_drop_threshold': 20,  # Higher threshold for peak season
                    'area_threshold': 15,  # Lower area threshold for sensitivity
                    'grid_size': 5,  # Smaller grid for precision
                },
                'severity': 'medium',
                'is_active': True,
                'cooldown_hours': 12,
                'notification_methods': ['email']
            },
            {
                'name': 'End of Season Analysis - Harvest Timing',
                'description': 'Monitors end of season NDVI decline to optimize harvest timing and detect premature senescence.',
                'scenario_type': 'phenology_delay',
                'parameters': {
                    'delay_threshold': 7,  # Days delay threshold
                    'phase': 'EOS',  # End of Season
                    'ndvi_threshold': 0.4,  # Higher threshold for EOS
                },
                'severity': 'low',
                'is_active': True,
                'cooldown_hours': 24,
                'notification_methods': ['email']
            }
        ]
