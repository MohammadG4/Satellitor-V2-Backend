from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from farmapp.models import VegetationIndexSet
from alerts.services import AlertManager


class Command(BaseCommand):
    help = 'Process alerts for recent vegetation index data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours-back',
            type=int,
            default=24,
            help='Process alerts for data from the last N hours (default: 24)'
        )
        parser.add_argument(
            '--land-id',
            type=int,
            help='Process alerts for a specific land ID only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without creating actual alerts'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Starting alert processing...')
        
        hours_back = options['hours_back']
        land_id = options.get('land_id')
        dry_run = options['dry_run']
        
        # Calculate time threshold
        time_threshold = timezone.now() - timedelta(hours=hours_back)
        
        # Get vegetation index sets to process
        queryset = VegetationIndexSet.objects.filter(
            created_at__gte=time_threshold
        ).select_related('land', 'land__user')
        
        if land_id:
            queryset = queryset.filter(land_id=land_id)
        
        vegetation_sets = queryset.order_by('land', 'acquisition_date')
        
        self.stdout.write(f'Found {vegetation_sets.count()} vegetation index sets to process')
        
        if dry_run:
            self.stdout.write('[DRY RUN] Would process alerts for:')
            for veg_set in vegetation_sets:
                self.stdout.write(f'  - Land {veg_set.land.name} ({veg_set.land.id}) - {veg_set.acquisition_date}')
            return
        
        # Process alerts
        alert_manager = AlertManager()
        processed_count = 0
        
        for veg_set in vegetation_sets:
            try:
                self.stdout.write(f'Processing alerts for land {veg_set.land.name} ({veg_set.acquisition_date})')
                alert_manager.process_new_vegetation_data(veg_set.land, veg_set)
                processed_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing alerts for land {veg_set.land.name}: {str(e)}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Alert processing completed! Processed {processed_count} vegetation index sets.')
        )
