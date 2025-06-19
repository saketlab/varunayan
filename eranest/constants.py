"""
Constants and configuration values for the eranest package.

This module contains all constants used throughout the package,
including variable mappings, pressure levels, and dataset configurations.
"""

from typing import Dict, List, Tuple
from enum import Enum

# ERA5 to Aurora variable name mappings
ERA5_TO_AURORA_SURFACE = {
    "2m_temperature": "2t",
    "10m_u_component_of_wind": "10u", 
    "10m_v_component_of_wind": "10v",
    "mean_sea_level_pressure": "msl",
}

ERA5_TO_AURORA_ATMOSPHERIC = {
    "temperature": "t",
    "u_component_of_wind": "u",
    "v_component_of_wind": "v",
    "specific_humidity": "q",
    "geopotential": "z",
}

ERA5_TO_AURORA_STATIC = {
    "geopotential": "z",
    "land_sea_mask": "lsm",
    "soil_type": "slt",
}

# Aurora standard pressure levels (hPa)
AURORA_PRESSURE_LEVELS = [
    "50", "100", "150", "200", "250", "300", "400", "500", 
    "600", "700", "850", "925", "1000"
]

# Default variable sets
DEFAULT_SURFACE_VARIABLES = [
    "2m_temperature",
    "10m_u_component_of_wind", 
    "10m_v_component_of_wind",
    "mean_sea_level_pressure",
]

DEFAULT_ATMOSPHERIC_VARIABLES = [
    "temperature",
    "u_component_of_wind",
    "v_component_of_wind", 
    "specific_humidity",
    "geopotential",
]

DEFAULT_STATIC_VARIABLES = [
    "geopotential",
    "land_sea_mask", 
    "soil_type",
]

# ERA5 dataset configurations
ERA5_DATASETS = {
    "surface": {
        "hourly": "reanalysis-era5-single-levels",
        "monthly": "reanalysis-era5-single-levels-monthly-means",
    },
    "pressure": {
        "hourly": "reanalysis-era5-pressure-levels", 
        "monthly": "reanalysis-era5-pressure-levels-monthly-means",
    }
}

# File format configurations
SUPPORTED_FILE_FORMATS = [".nc", ".zip", ".grib"]
SUPPORTED_JSON_FORMATS = [".json", ".geojson"]

# Performance settings
DEFAULT_CHUNK_SIZE = 1000
MAX_MEMORY_USAGE_MB = 4096
DEFAULT_PARALLEL_WORKERS = 4

# Spatial filtering optimization settings
SPATIAL_FILTER_CHUNK_SIZE = 10000
USE_SPATIAL_INDEX = True

# Validation thresholds
MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 360.0
MIN_PRESSURE_LEVEL = 1.0
MAX_PRESSURE_LEVEL = 1100.0

# Time format settings
DEFAULT_TIME_FORMAT = "%Y-%m-%d"
ISO_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

class DataFrequency(Enum):
    """Supported data frequencies."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class DatasetType(Enum):
    """ERA5 dataset types."""
    SURFACE = "surface"
    PRESSURE = "pressure"
    STATIC = "static"

class VariableType(Enum):
    """Variable categories."""
    SURFACE = "surface"
    ATMOSPHERIC = "atmospheric"
    STATIC = "static"

# Legacy variable mappings for backward compatibility
LEGACY_VARIABLE_MAPPING = {
    "t2m": "2m_temperature",
    "u10": "10m_u_component_of_wind",
    "v10": "10m_v_component_of_wind",
    "sp": "surface_pressure",
    "msl": "mean_sea_level_pressure",
    "tp": "total_precipitation",
    "d2m": "2m_dewpoint_temperature",
    "tcwv": "total_column_water_vapour",
    "tcc": "total_cloud_cover",
    "10si": "10m_wind_speed",
    "cape": "convective_available_potential_energy",
    "tcw": "total_column_water",
    "ssr": "surface_net_solar_radiation",
    "str": "surface_net_thermal_radiation",
    "sshf": "surface_sensible_heat_flux",
    "slhf": "surface_latent_heat_flux",
    "e": "evaporation",
    "ro": "runoff",
    "pev": "potential_evaporation",
    "src": "skin_reservoir_content",
    "sf": "snowfall",
    "sde": "snow_depth",
    "swvl1": "volumetric_soil_water_layer_1",
    "swvl2": "volumetric_soil_water_layer_2",
    "swvl3": "volumetric_soil_water_layer_3",
    "swvl4": "volumetric_soil_water_layer_4",
    "stl1": "soil_temperature_level_1",
    "stl2": "soil_temperature_level_2",
    "stl3": "soil_temperature_level_3",
    "stl4": "soil_temperature_level_4",
}

# Default grid resolutions (degrees)
DEFAULT_RESOLUTION = 0.25
SUPPORTED_RESOLUTIONS = [0.25, 0.5, 1.0, 2.5]

# Error messages
ERROR_MESSAGES = {
    "invalid_coordinates": "Invalid coordinates provided",
    "file_not_found": "File not found: {path}",
    "invalid_json": "Invalid JSON format in file: {path}",
    "no_data_found": "No data found for the specified criteria",
    "download_failed": "Download failed: {reason}",
    "processing_failed": "Data processing failed: {reason}",
    "invalid_date_range": "Invalid date range: start date must be before end date",
    "unsupported_format": "Unsupported file format: {format}",
}