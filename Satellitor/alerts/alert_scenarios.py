"""
Advanced Agricultural Alert Scenarios
Based on scientific research and industry best practices for precision agriculture
"""

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth import get_user_model
from farmapp.models import Land, VegetationIndexSet
from datetime import datetime, timedelta
from django.utils import timezone
import numpy as np
from typing import List, Dict, Tuple, Optional
import json

# Import scipy with fallback
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Fallback for basic statistics
    class stats:
        @staticmethod
        def linregress(x, y):
            # Simple linear regression fallback
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            
            # Calculate R-squared
            y_mean = sum_y / n
            ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
            ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
            r_value = (1 - ss_res / ss_tot) ** 0.5 if ss_tot > 0 else 0
            
            return slope, intercept, r_value, 0.05, 0  # p_value and std_err as 0.05 and 0

User = get_user_model()


# Models are defined in models.py to avoid conflicts


class AdvancedAlertProcessor:
    """Advanced alert processor for agricultural scenarios"""
    
    def __init__(self):
        self.logger = None  # Will be set by calling code
    
    def process_scenario(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Process a specific alert scenario"""
        try:
            if scenario.scenario_type == 'rapid_ndvi_drop':
                return self._process_rapid_ndvi_drop(scenario, vegetation_data)
            elif scenario.scenario_type == 'spatial_anomaly':
                return self._process_spatial_anomaly(scenario, vegetation_data)
            elif scenario.scenario_type == 'growth_stagnation':
                return self._process_growth_stagnation(scenario, vegetation_data)
            elif scenario.scenario_type == 'below_historical_percentile':
                return self._process_below_historical(scenario, vegetation_data)
            elif scenario.scenario_type == 'phenology_delay':
                return self._process_phenology_delay(scenario, vegetation_data)
            elif scenario.scenario_type == 'poor_emergence':
                return self._process_poor_emergence(scenario, vegetation_data)
            elif scenario.scenario_type == 'long_term_trend_decline':
                return self._process_trend_decline(scenario, vegetation_data)
            else:
                return {'triggered': False, 'message': 'Unknown scenario type'}
        except Exception as e:
            return {'triggered': False, 'error': str(e)}
    
    def _process_rapid_ndvi_drop(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Rapid NDVI drop detection (>10-20% drop vs previous 1-2 obs)"""
        params = scenario.parameters
        drop_threshold = params.get('drop_threshold', 15)  # Percentage
        lookback_obs = params.get('lookback_observations', 2)
        
        if len(vegetation_data) < lookback_obs + 1:
            return {'triggered': False, 'message': 'Insufficient data for comparison'}
        
        # Get recent NDVI values
        recent_data = sorted(vegetation_data, key=lambda x: x.acquisition_date)[-lookback_obs-1:]
        current_ndvi = self._get_index_value(recent_data[-1], 'NDVI')
        historical_ndvi = [self._get_index_value(data, 'NDVI') for data in recent_data[:-1]]
        
        if current_ndvi is None or any(v is None for v in historical_ndvi):
            return {'triggered': False, 'message': 'Missing NDVI data'}
        
        # Calculate percentage drop
        historical_median = np.median(historical_ndvi)
        drop_percentage = ((historical_median - current_ndvi) / historical_median) * 100
        
        triggered = drop_percentage > drop_threshold
        
        return {
            'triggered': triggered,
            'current_ndvi': current_ndvi,
            'historical_median': historical_median,
            'drop_percentage': drop_percentage,
            'threshold': drop_threshold,
            'message': f'NDVI dropped {drop_percentage:.1f}% vs historical median'
        }
    
    def _process_spatial_anomaly(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Spatial/patchy anomaly detection using true grid-based analysis of GeoTIFF pixels"""
        params = scenario.parameters
        anomaly_threshold_percent = params.get('anomaly_threshold_percent', 15.0)  # NDVI drop threshold
        area_threshold_percent = params.get('area_threshold_percent', 20.0)  # Percentage of field area
        grid_size_meters = params.get('grid_size_meters', 10)  # Grid cell size in meters
        min_ndvi_value = params.get('min_ndvi_value', 0.1)  # Minimum NDVI to consider
        
        if not vegetation_data:
            return {'triggered': False, 'message': 'No vegetation data available'}
        
        latest_data = max(vegetation_data, key=lambda x: x.acquisition_date)
        
        # Get previous data for comparison
        previous_data = None
        if len(vegetation_data) > 1:
            sorted_data = sorted(vegetation_data, key=lambda x: x.acquisition_date, reverse=True)
            previous_data = sorted_data[1]
        
        if not previous_data:
            return {'triggered': False, 'message': 'Need previous data for spatial anomaly detection'}
        
        try:
            import os
            # Check if GeoTIFF files exist
            current_file = latest_data.file_path
            previous_file = previous_data.file_path
            
            if not os.path.exists(current_file) or not os.path.exists(previous_file):
                # Fallback to statistical analysis if files don't exist
                return self._fallback_spatial_analysis(latest_data, previous_data, anomaly_threshold_percent, area_threshold_percent)
            
            # Analyze GeoTIFF for spatial anomalies
            anomaly_result = self._analyze_spatial_anomaly(
                latest_data, 
                previous_data, 
                grid_size_meters,
                anomaly_threshold_percent,
                min_ndvi_value
            )
            
            if anomaly_result is None:
                return self._fallback_spatial_analysis(latest_data, previous_data, anomaly_threshold_percent, area_threshold_percent)
            
            anomaly_area_percent = anomaly_result['anomaly_area_percent']
            triggered = anomaly_area_percent > area_threshold_percent
            
            return {
                'triggered': triggered,
                'anomaly_area_percent': anomaly_area_percent,
                'area_threshold_percent': area_threshold_percent,
                'anomaly_cells_count': anomaly_result['anomaly_cells_count'],
                'total_cells_count': anomaly_result['total_cells_count'],
                'grid_size_meters': grid_size_meters,
                'anomaly_threshold_percent': anomaly_threshold_percent,
                'hotspot_cells': anomaly_result.get('hotspot_cells', []),
                'message': f'{anomaly_area_percent:.1f}% of field area shows NDVI drop >{anomaly_threshold_percent}%'
            }
            
        except Exception as e:
            return {'triggered': False, 'message': f'Error analyzing spatial anomaly: {str(e)}'}
    
    def _analyze_spatial_anomaly(self, current_data, previous_data, grid_size_meters, 
                                anomaly_threshold_percent, min_ndvi_value):
        """Analyze GeoTIFF for spatial anomalies using grid-based approach"""
        import os
        import rasterio
        import numpy as np
        from rasterio.warp import transform_bounds
        from rasterio.features import rasterize
        from shapely.geometry import box
        
        current_file = current_data.file_path
        previous_file = previous_data.file_path
        
        if not os.path.exists(current_file) or not os.path.exists(previous_file):
            return None
        
        try:
            with rasterio.open(current_file) as current_src, rasterio.open(previous_file) as previous_src:
                # Read NDVI bands (band 1)
                current_ndvi = current_src.read(1)
                previous_ndvi = previous_src.read(1)
                
                # Get geospatial bounds
                current_bounds = current_src.bounds
                previous_bounds = previous_src.bounds
                
                # Use the intersection of both rasters
                min_x = max(current_bounds.left, previous_bounds.left)
                max_x = min(current_bounds.right, previous_bounds.right)
                min_y = max(current_bounds.bottom, previous_bounds.bottom)
                max_y = min(current_bounds.top, previous_bounds.top)
                
                # Convert grid size from meters to pixels
                pixel_size_x = (current_bounds.right - current_bounds.left) / current_ndvi.shape[1]
                pixel_size_y = (current_bounds.top - current_bounds.bottom) / current_ndvi.shape[0]
                
                grid_pixels_x = max(1, int(grid_size_meters / pixel_size_x))
                grid_pixels_y = max(1, int(grid_size_meters / pixel_size_y))
                
                # Create grid cells
                height, width = current_ndvi.shape
                anomaly_cells = 0
                total_cells = 0
                hotspot_cells = []
                
                for i in range(0, height, grid_pixels_y):
                    for j in range(0, width, grid_pixels_x):
                        # Define grid cell bounds
                        end_i = min(i + grid_pixels_y, height)
                        end_j = min(j + grid_pixels_x, width)
                        
                        # Extract cell data
                        current_cell = current_ndvi[i:end_i, j:end_j]
                        previous_cell = previous_ndvi[i:end_i, j:end_j]
                        
                        # Filter valid data (not NaN, not NoData)
                        current_valid = current_cell[~np.isnan(current_cell) & (current_cell > min_ndvi_value)]
                        previous_valid = previous_cell[~np.isnan(previous_cell) & (previous_cell > min_ndvi_value)]
                        
                        if len(current_valid) > 0 and len(previous_valid) > 0:
                            # Calculate mean NDVI for this cell
                            current_mean = np.mean(current_valid)
                            previous_mean = np.mean(previous_valid)
                            
                            # Calculate percentage change
                            if previous_mean > 0:
                                percent_change = ((current_mean - previous_mean) / previous_mean) * 100
                                
                                # Check if this cell shows anomaly
                                if percent_change < -anomaly_threshold_percent:
                                    anomaly_cells += 1
                                    
                                    # Store hotspot cell info
                                    cell_center_x = (j + end_j) / 2
                                    cell_center_y = (i + end_i) / 2
                                    hotspot_cells.append({
                                        'x': int(cell_center_x),
                                        'y': int(cell_center_y),
                                        'percent_change': float(percent_change),
                                        'current_ndvi': float(current_mean),
                                        'previous_ndvi': float(previous_mean)
                                    })
                            
                            total_cells += 1
                
                if total_cells == 0:
                    return None
                
                anomaly_area_percent = (anomaly_cells / total_cells) * 100
                
                return {
                    'anomaly_area_percent': anomaly_area_percent,
                    'anomaly_cells_count': anomaly_cells,
                    'total_cells_count': total_cells,
                    'hotspot_cells': hotspot_cells[:10]  # Limit to top 10 hotspots
                }
                
        except Exception as e:
            print(f"Error in spatial analysis: {e}")
            return None
    
    def _fallback_spatial_analysis(self, current_data, previous_data, anomaly_threshold_percent, area_threshold_percent):
        """Fallback spatial analysis using statistical data when GeoTIFF files are not available"""
        current_ndvi = self._get_index_value(current_data, 'NDVI')
        previous_ndvi = self._get_index_value(previous_data, 'NDVI')
        
        if current_ndvi is None or previous_ndvi is None:
            return {'triggered': False, 'message': 'No valid NDVI data for spatial analysis'}
        
        # Calculate percentage change
        if previous_ndvi > 0:
            percent_change = ((current_ndvi - previous_ndvi) / previous_ndvi) * 100
        else:
            percent_change = 0
        
        # Simulate spatial analysis based on NDVI statistics
        # If there's a significant drop, assume some areas are affected
        if percent_change < -anomaly_threshold_percent:
            # Simulate that a portion of the field shows the anomaly
            simulated_anomaly_percent = min(abs(percent_change) / 2, 50)  # Cap at 50%
            triggered = simulated_anomaly_percent > area_threshold_percent
        else:
            simulated_anomaly_percent = 0
            triggered = False
        
        return {
            'triggered': triggered,
            'anomaly_area_percent': simulated_anomaly_percent,
            'area_threshold_percent': area_threshold_percent,
            'anomaly_cells_count': int(simulated_anomaly_percent * 10),  # Simulate cell count
            'total_cells_count': 100,  # Simulate total cells
            'grid_size_meters': 10,
            'anomaly_threshold_percent': anomaly_threshold_percent,
            'hotspot_cells': [],
            'message': f'Fallback analysis: {simulated_anomaly_percent:.1f}% of field area shows NDVI drop >{anomaly_threshold_percent}%'
        }
    
    def _process_growth_stagnation(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Growth stagnation detection (NDVI should increase but stays flat/decreases)"""
        params = scenario.parameters
        min_slope_threshold = params.get('min_slope_threshold', 0.01)  # Minimum expected slope
        stagnation_days = params.get('stagnation_days', 10)  # Minimum days of stagnation
        min_observations = params.get('min_observations', 3)  # Minimum observations needed
        
        if len(vegetation_data) < min_observations:
            return {'triggered': False, 'message': f'Insufficient data for trend analysis (need {min_observations}, have {len(vegetation_data)})'}
        
        # Use the most recent data available (don't restrict by date)
        recent_data = sorted(vegetation_data, key=lambda x: x.acquisition_date, reverse=True)[:10]  # Last 10 observations
        recent_data = sorted(recent_data, key=lambda x: x.acquisition_date)  # Sort chronologically
        
        # Extract NDVI values and dates
        ndvi_values = []
        dates = []
        for data in recent_data:
            ndvi = self._get_index_value(data, 'NDVI')
            if ndvi is not None:
                ndvi_values.append(ndvi)
                dates.append((data.acquisition_date - recent_data[0].acquisition_date).days)
        
        if len(ndvi_values) < min_observations:
            return {'triggered': False, 'message': f'Insufficient valid NDVI data (need {min_observations}, have {len(ndvi_values)})'}
        
        # Calculate linear trend
        try:
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(dates, ndvi_values)
        except ImportError:
            # Fallback if scipy not available
            slope = (ndvi_values[-1] - ndvi_values[0]) / (dates[-1] - dates[0]) if len(dates) > 1 else 0
            r_value = 0
        
        # Check if slope is below threshold for sufficient time
        days_below_threshold = 0
        for i in range(1, len(ndvi_values)):
            if ndvi_values[i] <= ndvi_values[i-1] + min_slope_threshold:
                days_below_threshold += (dates[i] - dates[i-1])
            else:
                days_below_threshold = 0
        
        triggered = slope < min_slope_threshold and days_below_threshold >= stagnation_days
        
        # Calculate days analyzed
        days_analyzed = dates[-1] - dates[0] if len(dates) > 1 else 0
        
        return {
            'triggered': triggered,
            'slope': slope,
            'min_slope_threshold': min_slope_threshold,
            'days_below_threshold': days_below_threshold,
            'stagnation_days': stagnation_days,
            'data_points': len(ndvi_values),
            'days_analyzed': days_analyzed,
            'r_squared': r_value ** 2,
            'message': f'NDVI slope {slope:.4f} below threshold {min_slope_threshold} for {days_below_threshold} days'
        }
    
    def _process_below_historical(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Below historical percentile detection (drought early warning)"""
        params = scenario.parameters
        percentile_threshold = params.get('percentile_threshold', 10)  # Below 10th percentile
        historical_years = params.get('historical_years', 3)  # Years of historical data
        
        if not vegetation_data:
            return {'triggered': False, 'message': 'No vegetation data available'}
        
        latest_data = max(vegetation_data, key=lambda x: x.acquisition_date)
        current_ndvi = self._get_index_value(latest_data, 'NDVI')
        
        if current_ndvi is None:
            return {'triggered': False, 'message': 'No current NDVI data'}
        
        # Get historical data for same week of year
        from datetime import datetime
        current_date = latest_data.acquisition_date
        current_week = datetime.combine(current_date, datetime.min.time()).isocalendar()[1]
        historical_ndvi_values = []
        
        for data in vegetation_data:
            data_week = datetime.combine(data.acquisition_date, datetime.min.time()).isocalendar()[1]
            if data_week == current_week:
                ndvi = self._get_index_value(data, 'NDVI')
                if ndvi is not None:
                    historical_ndvi_values.append(ndvi)
        
        if len(historical_ndvi_values) < 5:  # Need minimum historical data
            return {'triggered': False, 'message': 'Insufficient historical data'}
        
        # Calculate percentile
        historical_percentile = np.percentile(historical_ndvi_values, percentile_threshold)
        triggered = current_ndvi < historical_percentile
        
        return {
            'triggered': triggered,
            'current_ndvi': current_ndvi,
            'historical_percentile': historical_percentile,
            'percentile_threshold': percentile_threshold,
            'historical_count': len(historical_ndvi_values),
            'message': f'Current NDVI {current_ndvi:.3f} below {percentile_threshold}th percentile {historical_percentile:.3f}'
        }
    
    def _process_phenology_delay(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Phenology delay detection (SOS/EOS deviation) using current crop planting_date"""
        params = scenario.parameters
        delay_threshold_days = params.get('delay_threshold_days', 14)  # Days
        sos_threshold = params.get('sos_threshold', 0.3)  # NDVI threshold for SOS detection
        min_observations = params.get('min_observations', 5)  # Minimum observations needed
        
        if len(vegetation_data) < min_observations:
            return {'triggered': False, 'message': 'Insufficient data for phenology analysis'}
        
        # Get current crop instance planting date
        land = scenario.land
        current_crop = land.crop_instances.filter(harvest_date__isnull=True).order_by('-planting_date').first()
        
        if not current_crop or not current_crop.planting_date:
            return {'triggered': False, 'message': 'No active crop with planting date found for this land'}
        
        planting_date = current_crop.planting_date
        
        # Sort data by date
        sorted_data = sorted(vegetation_data, key=lambda x: x.acquisition_date)
        
        # Detect Start of Season (SOS) - when NDVI first exceeds threshold after planting
        sos_date = self._detect_start_of_season(sorted_data, planting_date, sos_threshold)
        
        if sos_date is None:
            return {'triggered': False, 'message': 'Could not detect Start of Season'}
        
        # Calculate expected SOS date (typically 7-14 days after planting for most crops)
        expected_sos_date = planting_date + timedelta(days=10)  # Default expectation
        
        # Calculate delay
        delay_days = (sos_date - expected_sos_date).days
        triggered = delay_days > delay_threshold_days
        
        return {
            'triggered': triggered,
            'planting_date': planting_date.isoformat(),
            'crop_name': current_crop.crop.crop_name,
            'sos_date': sos_date.isoformat(),
            'expected_sos_date': expected_sos_date.isoformat(),
            'delay_days': delay_days,
            'delay_threshold_days': delay_threshold_days,
            'sos_threshold': sos_threshold,
            'message': f'Start of Season delayed by {delay_days} days for {current_crop.crop.crop_name} (threshold: {delay_threshold_days})'
        }
    
    def _process_poor_emergence(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Poor emergence detection (low NDVI after planting) using current crop planting_date"""
        params = scenario.parameters
        emergence_threshold = params.get('emergence_threshold', 0.2)  # NDVI threshold
        days_after_planting = params.get('days_after_sowing', 21)  # Days to check (keeping parameter name for compatibility)
        min_ndvi_value = params.get('min_ndvi_value', 0.1)  # Minimum NDVI to consider
        
        # Get current crop instance planting date
        land = scenario.land
        current_crop = land.crop_instances.filter(harvest_date__isnull=True).order_by('-planting_date').first()
        
        if not current_crop or not current_crop.planting_date:
            return {'triggered': False, 'message': 'No active crop with planting date found for this land'}
        
        planting_date = current_crop.planting_date
        
        # Get data after planting
        post_planting_data = [d for d in vegetation_data if d.acquisition_date >= planting_date]
        
        if not post_planting_data:
            return {'triggered': False, 'message': 'No data available after planting'}
        
        # Check if NDVI remains below threshold for the specified period
        low_ndvi_count = 0
        total_observations = 0
        
        for data in post_planting_data:
            # Only check data within the specified days after planting
            days_since_planting = (data.acquisition_date - planting_date).days
            if days_since_planting <= days_after_planting:
                ndvi = self._get_index_value(data, 'NDVI')
                if ndvi is not None and ndvi >= min_ndvi_value:  # Valid NDVI data
                    total_observations += 1
                    if ndvi < emergence_threshold:
                        low_ndvi_count += 1
        
        if total_observations == 0:
            return {'triggered': False, 'message': 'No valid NDVI data after planting'}
        
        # Trigger if most observations show low NDVI
        low_ndvi_percentage = (low_ndvi_count / total_observations) * 100
        triggered = low_ndvi_percentage > 70  # 70% of observations below threshold
        
        return {
            'triggered': triggered,
            'planting_date': planting_date.isoformat(),
            'crop_name': current_crop.crop.crop_name,
            'days_after_planting': days_after_planting,
            'low_ndvi_count': low_ndvi_count,
            'total_observations': total_observations,
            'low_ndvi_percentage': low_ndvi_percentage,
            'emergence_threshold': emergence_threshold,
            'min_ndvi_value': min_ndvi_value,
            'message': f'{low_ndvi_percentage:.1f}% of observations below {emergence_threshold} NDVI after planting {current_crop.crop.crop_name}'
        }
    
    def _detect_start_of_season(self, sorted_data, planting_date, sos_threshold):
        """Detect Start of Season (SOS) - when NDVI first exceeds threshold after planting"""
        for data in sorted_data:
            if data.acquisition_date >= planting_date:
                ndvi = self._get_index_value(data, 'NDVI')
                if ndvi is not None and ndvi >= sos_threshold:
                    return data.acquisition_date
        return None
    
    def _process_trend_decline(self, scenario, vegetation_data: List[VegetationIndexSet]) -> Dict:
        """Long-term trend decline detection (chronic degradation)"""
        params = scenario.parameters
        min_years = params.get('min_years', 2)  # Minimum years for trend analysis
        significance_level = params.get('significance_level', 0.05)  # Statistical significance
        
        if len(vegetation_data) < 10:
            return {'triggered': False, 'message': 'Insufficient data for trend analysis'}
        
        # Group data by year and calculate seasonal peaks
        yearly_peaks = {}
        for data in vegetation_data:
            year = data.acquisition_date.year
            ndvi = self._get_index_value(data, 'NDVI')
            if ndvi is not None:
                if year not in yearly_peaks:
                    yearly_peaks[year] = []
                yearly_peaks[year].append(ndvi)
        
        # Calculate peak NDVI for each year
        yearly_max_ndvi = {year: max(values) for year, values in yearly_peaks.items()}
        
        if len(yearly_max_ndvi) < min_years:
            return {'triggered': False, 'message': f'Need at least {min_years} years of data'}
        
        # Perform Mann-Kendall trend test
        years = sorted(yearly_max_ndvi.keys())
        ndvi_values = [yearly_max_ndvi[year] for year in years]
        
        # Simplified trend calculation (in real implementation, use proper Mann-Kendall)
        slope, intercept, r_value, p_value, std_err = stats.linregress(years, ndvi_values)
        
        triggered = slope < 0 and p_value < significance_level
        
        return {
            'triggered': triggered,
            'slope': slope,
            'p_value': p_value,
            'significance_level': significance_level,
            'years_analyzed': len(years),
            'r_squared': r_value ** 2,
            'message': f'Long-term NDVI trend: {slope:.4f} per year (p={p_value:.4f})'
        }
    
    def _get_index_value(self, vegetation_data: VegetationIndexSet, index_name: str) -> Optional[float]:
        """Get index value from vegetation data"""
        try:
            stats = vegetation_data.stats.get(index_name, {})
            return stats.get('mean')
        except:
            return None
    
    def _detect_phenology_phase(self, sorted_data: List[VegetationIndexSet], phase: str, threshold: float) -> Optional[datetime.date]:
        """Detect phenology phase (simplified implementation)"""
        if phase == 'SOS':  # Start of Season
            for data in sorted_data:
                ndvi = self._get_index_value(data, 'NDVI')
                if ndvi is not None and ndvi > threshold:
                    return data.acquisition_date
        elif phase == 'EOS':  # End of Season
            for data in reversed(sorted_data):
                ndvi = self._get_index_value(data, 'NDVI')
                if ndvi is not None and ndvi > threshold:
                    return data.acquisition_date
        return None
    
    def _get_expected_phase_date(self, first_date: datetime.date, phase: str) -> Optional[datetime.date]:
        """Get expected phase date (simplified - would use historical data)"""
        # This is a simplified implementation
        # In real implementation, would use historical phenology data
        if phase == 'SOS':
            return first_date + timedelta(days=30)  # Expected 30 days after first observation
        elif phase == 'EOS':
            return first_date + timedelta(days=200)  # Expected 200 days after first observation
        return None
