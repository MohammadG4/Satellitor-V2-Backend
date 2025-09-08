# Satellite Data Pipeline Setup

## Overview
This pipeline fetches satellite data from Copernicus API every 5 days for all active lands and processes the GeoTIFF files to extract vegetation indices.

## Features
- **OAuth Authentication**: Automatic token refresh from Copernicus
- **Smart Date Ranges**: 5-day intervals (1-5, 6-10, 11-15, etc.)
- **New Land Detection**: Fetches from start of month for new lands
- **Band Processing**: Extracts NDVI, NDRE, EVI, SAVI, GCI statistics
- **File Organization**: `indices_data/<land_id>/<date>.tiff`
- **Database Integration**: Auto-saves to `VegetationIndexSet` model

## Setup Instructions

### 1. Install Dependencies
```bash
docker compose build web
docker compose up -d web
```

### 2. Test the Command
```bash
# Dry run to test without making API calls
docker compose exec web python Satellitor/manage.py fetch_satellite_data --dry-run

# Test with actual API calls
docker compose exec web python Satellitor/manage.py fetch_satellite_data

# Force fetch for all lands (even if they have recent data)
docker compose exec web python Satellitor/manage.py fetch_satellite_data --force-all
```

### 3. Set Up Cron Job (Every 5 Days)
Add this to your crontab:
```bash
# Run every 5 days at 2 AM
0 2 */5 * * cd /path/to/Satellitor-V2 && docker compose exec web python Satellitor/manage.py fetch_satellite_data
```

### 4. Environment Variables
The following are already configured in `docker-compose.yml`:
- `COPERNICUS_CLIENT_ID`: Your Copernicus client ID
- `COPERNICUS_CLIENT_SECRET`: Your Copernicus client secret

## File Structure Created
```
indices_data/
├── 1/                    # Land ID 1
│   ├── 2025-01-08.tiff
│   └── 2025-01-13.tiff
├── 2/                    # Land ID 2
│   └── 2025-01-08.tiff
└── ...
```

## Band Mapping
The GeoTIFF bands are mapped as follows:
- Band 1: NDVI
- Band 2: NDRE  
- Band 3: EVI
- Band 4: SAVI
- Band 5: GCI

## Database Updates
Each run creates/updates `VegetationIndexSet` records with:
- `land`: Reference to the land
- `acquisition_date`: Date of the satellite data
- `file_path`: Path to the saved GeoTIFF file
- `stats`: JSON containing min/max/mean for each vegetation index

## Monitoring
Check logs for:
- API request success/failure
- File processing errors
- Database update status

## How It Works

### Date Range Logic
- **New Lands**: Fetches data from start of current month to present
- **Existing Lands**: Fetches data in 5-day intervals from last acquisition date
- **Smart Intervals**: 1-5, 6-10, 11-15, 16-20, 21-25, 26-30/31

### Band Processing
The GeoTIFF contains 5 bands with vegetation indices:
- **Band 1**: NDVI (Normalized Difference Vegetation Index)
- **Band 2**: NDRE (Normalized Difference Red Edge)
- **Band 3**: EVI (Enhanced Vegetation Index)
- **Band 4**: SAVI (Soil Adjusted Vegetation Index)
- **Band 5**: GCI (Green Chlorophyll Index)

### Statistics Extracted
For each band, the system extracts:
- `min`: Minimum value
- `max`: Maximum value
- `mean`: Average value
- `std`: Standard deviation
- `count`: Number of valid pixels

### API Integration
- Uses OAuth 2.0 client credentials flow
- Automatically handles token refresh
- Sends land boundary as GeoJSON polygon
- Requests Sentinel-2 L2A data with max 20% cloud coverage
- Processes data using custom evalscript for vegetation indices

## Monitoring
Check logs for:
- API authentication success/failure
- Data fetch progress per land
- File processing and database updates
- Error handling and recovery
