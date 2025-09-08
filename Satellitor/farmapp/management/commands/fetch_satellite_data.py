import os
import requests
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from farmapp.models import Land, VegetationIndexSet
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
import base64


class Command(BaseCommand):
    help = 'Fetch satellite data for all lands from Copernicus API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-back',
            type=int,
            default=5,
            help='Number of days back to fetch data for (default: 5)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making actual API calls or saving files'
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Force fetch data for all lands, even if they already have recent data'
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting satellite data fetch...')
        
        # Create indices_data directory structure
        base_dir = os.path.join(settings.BASE_DIR, 'indices_data')
        os.makedirs(base_dir, exist_ok=True)
        
        # Get all active lands
        lands = Land.objects.filter(status=True)
        self.stdout.write(f'Found {lands.count()} active lands')
        
        days_back = options['days_back']
        dry_run = options['dry_run']
        force_all = options['force_all']
        
        # Get access token
        access_token = self.get_access_token()
        if not access_token:
            self.stdout.write(self.style.ERROR('Failed to get access token'))
            return
        
        for land in lands:
            self.stdout.write(f'Processing land: {land.name} (ID: {land.id})')
            
            # Calculate date ranges for this month
            date_ranges = self.calculate_date_ranges(land, force_all)
            
            for start_date, end_date in date_ranges:
                try:
                    if dry_run:
                        self.stdout.write(f'[DRY RUN] Would fetch data for {land.name} from {start_date} to {end_date}')
                        continue
                    
                    # Fetch data for this land and date range
                    self.fetch_land_data(land, start_date, end_date, base_dir, access_token)
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing land {land.name} for {start_date} to {end_date}: {str(e)}')
                    )
                    continue
        
        self.stdout.write(self.style.SUCCESS('Satellite data fetch completed!'))

    def get_access_token(self):
        """Get access token from Copernicus OAuth"""
        token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        
        # Get credentials from environment variables
        client_id = os.getenv('COPERNICUS_CLIENT_ID', 'sh-89762f29-a69e-4d90-afa7-06a9d461af7e')
        client_secret = os.getenv('COPERNICUS_CLIENT_SECRET', 'pJUkbAINzJSxvWOB7Cqr1oML1F6CSHgX')
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get access token: {str(e)}'))
            return None

    def calculate_date_ranges(self, land, force_all):
        """Calculate date ranges for fetching data in 5-day intervals"""
        today = datetime.now().date()
        current_month = today.replace(day=1)
        
        # Check if land has any existing data
        existing_data = VegetationIndexSet.objects.filter(land=land).order_by('-acquisition_date')
        
        if not existing_data.exists() or force_all:
            # New land or force all - get data from start of current month in 5-day ranges
            return self.get_monthly_ranges(current_month, today)
        else:
            # Existing land - get data from last acquisition date
            last_acquisition = existing_data.first().acquisition_date
            if last_acquisition >= today:
                return []  # Already have today's data
            
            # Create 5-day ranges from last acquisition to today
            ranges = []
            current_start = last_acquisition + timedelta(days=1)
            
            while current_start <= today:
                # Find the start of the 5-day period containing current_start
                day_of_month = current_start.day
                period_start_day = ((day_of_month - 1) // 5) * 5 + 1
                period_start = current_start.replace(day=period_start_day)
                
                # Calculate period end (5 days later, but not beyond month end)
                period_end = min(period_start + timedelta(days=4), today)
                
                ranges.append((period_start, period_end))
                
                # Move to next 5-day period
                next_period_start = period_end + timedelta(days=1)
                if next_period_start > today:
                    break
                current_start = next_period_start
            
            return ranges

    def get_monthly_ranges(self, month_start, today):
        """Get 5-day ranges for a month: 1-5, 6-10, 11-15, 16-20, 21-25, 26-30/31"""
        ranges = []
        
        # 1-5
        if month_start <= today:
            end_1_5 = min(month_start + timedelta(days=4), today)
            ranges.append((month_start, end_1_5))
        
        # 6-10
        start_6_10 = month_start + timedelta(days=5)
        if start_6_10 <= today:
            end_6_10 = min(start_6_10 + timedelta(days=4), today)
            ranges.append((start_6_10, end_6_10))
        
        # 11-15
        start_11_15 = month_start + timedelta(days=10)
        if start_11_15 <= today:
            end_11_15 = min(start_11_15 + timedelta(days=4), today)
            ranges.append((start_11_15, end_11_15))
        
        # 16-20
        start_16_20 = month_start + timedelta(days=15)
        if start_16_20 <= today:
            end_16_20 = min(start_16_20 + timedelta(days=4), today)
            ranges.append((start_16_20, end_16_20))
        
        # 21-25
        start_21_25 = month_start + timedelta(days=20)
        if start_21_25 <= today:
            end_21_25 = min(start_21_25 + timedelta(days=4), today)
            ranges.append((start_21_25, end_21_25))
        
        # 26-30/31
        start_26_30 = month_start + timedelta(days=25)
        if start_26_30 <= today:
            end_26_30 = min(start_26_30 + timedelta(days=4), today)
            ranges.append((start_26_30, end_26_30))
        
        return ranges

    def fetch_land_data(self, land, start_date, end_date, base_dir, access_token):
        """Fetch satellite data for a specific land"""
        
        # Get land boundary as GeoJSON
        if not land.boundary:
            self.stdout.write(f'Land {land.name} has no boundary, skipping...')
            return
            
        # Convert boundary to GeoJSON and ensure proper CRS
        boundary_geojson = land.boundary.geojson
        boundary_data = json.loads(boundary_geojson)
        
        # Prepare API request payload
        payload = {
            "input": {
                "bounds": {
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    },
                    "geometry": boundary_data
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{start_date}T00:00:00Z",
                                "to": f"{end_date}T23:59:59Z"
                            },
                            "maxCloudCoverage": 20
                        },
                        "mosaicking": "leastCC"
                    }
                ]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [
                    {
                        "identifier": "all_indices",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": """//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "B05", "B08"],
    output: [{ id: "all_indices", bands: 5, sampleType: "FLOAT32" }]
  };
}

function evaluatePixel(s) {
  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
  let ndre = (s.B08 - s.B05) / (s.B08 + s.B05);
  let evi = 2.5 * (s.B08 - s.B04) / (s.B08 + 6.0 * s.B04 - 7.5 * s.B02 + 1.0);
  let savi = (1.5 * (s.B08 - s.B04)) / (s.B08 + s.B04 + 0.5);
  let gci = (s.B08 / s.B03) - 1.0;
  return [ndvi, ndre, evi, savi, gci];
}"""
        }
        
        # Make API request
        api_url = "https://sh.dataspace.copernicus.eu/api/v1/process"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        self.stdout.write(f'Requesting data for {land.name} from {start_date} to {end_date}...')
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            self.stdout.write(
                self.style.ERROR(f'API request failed for {land.name}: {response.status_code} - {response.text}')
            )
            return
        
        # Process the response
        self.process_api_response(land, response, base_dir, start_date)

    def process_api_response(self, land, response, base_dir, acquisition_date):
        """Process the API response and save GeoTIFF file"""
        
        # Create land-specific directory
        land_dir = os.path.join(base_dir, str(land.id))
        os.makedirs(land_dir, exist_ok=True)
        
        # Save GeoTIFF file
        filename = f"{acquisition_date.isoformat()}.tiff"
        file_path = os.path.join(land_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        self.stdout.write(f'Saved GeoTIFF: {file_path}')
        
        # Process the GeoTIFF to extract band statistics
        stats = self.extract_band_statistics(file_path)
        
        # Save to database
        vegetation_index_set, created = VegetationIndexSet.objects.update_or_create(
            land=land,
            acquisition_date=acquisition_date,
            defaults={
                'file_path': file_path,
                'stats': stats
            }
        )
        
        if created:
            self.stdout.write(f'Created new VegetationIndexSet for {land.name} on {acquisition_date}')
        else:
            self.stdout.write(f'Updated VegetationIndexSet for {land.name} on {acquisition_date}')

    def extract_band_statistics(self, file_path):
        """Extract min, max, mean statistics from each band of the GeoTIFF"""
        
        stats = {}
        band_mapping = {
            1: 'NDVI',
            2: 'NDRE', 
            3: 'EVI',
            4: 'SAVI',
            5: 'GCI'
        }
        
        try:
            with rasterio.open(file_path) as src:
                for band_num, index_name in band_mapping.items():
                    if band_num <= src.count:
                        band_data = src.read(band_num)
                        
                        # Remove NoData values (assuming NaN or very negative values are NoData)
                        # Also handle potential division by zero in vegetation index calculations
                        valid_mask = ~np.isnan(band_data) & (band_data > -10) & (band_data < 10)
                        valid_data = band_data[valid_mask]
                        
                        if len(valid_data) > 0:
                            stats[index_name] = {
                                'min': float(np.min(valid_data)),
                                'max': float(np.max(valid_data)),
                                'mean': float(np.mean(valid_data)),
                                'std': float(np.std(valid_data)),
                                'count': int(len(valid_data))
                            }
                        else:
                            stats[index_name] = {
                                'min': 0.0,
                                'max': 0.0,
                                'mean': 0.0,
                                'std': 0.0,
                                'count': 0
                            }
                            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing GeoTIFF {file_path}: {str(e)}')
            )
            # Return default stats if processing fails
            for index_name in band_mapping.values():
                stats[index_name] = {
                    'min': 0.0,
                    'max': 0.0,
                    'mean': 0.0,
                    'std': 0.0,
                    'count': 0
                }
        
        return stats
