import os
import sys
import json
import zipfile
import cdsapi
import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from typing import Dict, Tuple, List, Union, Optional
import datetime as dt
from dateutil.relativedelta import relativedelta
import math
import time

def extract_coords_from_geometry(geometry: Dict) -> List[List[float]]:
    """Extract all coordinates from a GeoJSON geometry object."""
    coords = []
    geom_type = geometry['type']
    
    if geom_type == 'Point':
        # Convert [lon, lat] to [lon, lat] (no change needed, but be explicit)
        coords.append(geometry['coordinates'])
    elif geom_type == 'MultiPoint' or geom_type == 'LineString':
        coords.extend(geometry['coordinates'])
    elif geom_type == 'MultiLineString' or geom_type == 'Polygon':
        for line in geometry['coordinates']:
            coords.extend(line)
    elif geom_type == 'MultiPolygon':
        for polygon in geometry['coordinates']:
            for line in polygon:
                coords.extend(line)
    elif geom_type == 'GeometryCollection':
        for geom in geometry['geometries']:
            coords.extend(extract_coords_from_geometry(geom))
    
    return coords

def get_bounding_box(geojson_data: Dict) -> Tuple[float, float, float, float]:
    """
    Extract the bounding box (west, south, east, north) from a GeoJSON object.
    
    Args:
        geojson_data: A GeoJSON object (loaded as a Python dictionary)
        
    Returns:
        Tuple of (west, south, east, north) coordinates
    """
    # Check if the GeoJSON already has a bbox property
    if 'bbox' in geojson_data:
        bbox = geojson_data['bbox']
        # GeoJSON bbox format is [west, south, east, north]
        return (bbox[0], bbox[1], bbox[2], bbox[3])
    
    # If no bbox, calculate it ourselves
    all_coords = []
    
    if geojson_data['type'] == 'Feature':
        all_coords.extend(extract_coords_from_geometry(geojson_data['geometry']))
    elif geojson_data['type'] == 'FeatureCollection':
        for feature in geojson_data['features']:
            all_coords.extend(extract_coords_from_geometry(feature['geometry']))
    else:
        # Assume it's a geometry object
        all_coords.extend(extract_coords_from_geometry(geojson_data))
    
    if not all_coords:
        raise ValueError("No coordinates found in the GeoJSON data")
    
    # Extract longitudes (x) and latitudes (y) - IMPORTANT: GeoJSON stores [lon, lat]
    lons = [coord[0] for coord in all_coords]  # Longitude is first
    lats = [coord[1] for coord in all_coords]  # Latitude is second
    
    # Calculate bounds
    west = min(lons)
    east = max(lons)
    south = min(lats)
    north = max(lats)
    
    return (west, south, east, north)

def setup_cdsapi_config():
    """Set up CDS API configuration file."""
    api_key = input("Enter your CDS API key/token (the long string after the colon): ").strip()
    cds_file = os.path.expanduser("~/.cdsapirc")
        
    with open(cds_file, "w") as f:
        f.write("url: https://cds.climate.copernicus.eu/api\n")
        f.write(f"key: {api_key}\n")
    print(f"CDS API credentials saved to: {cds_file}")

def find_netcdf_files(extraction_dir: str) -> List[str]:
    """
    Find all NetCDF files in the extraction directory, 
    including nested directories.
    
    Args:
        extraction_dir: Directory to search for NetCDF files
    
    Returns:
        List of full paths to NetCDF files
    """
    nc_files = []
    for root, _, files in os.walk(extraction_dir):
        nc_files.extend([
            os.path.join(root, file) 
            for file in files 
            if file.endswith('.nc')
        ])
    return nc_files
def extract_download(zip_or_file_path: str, extract_dir: str = None) -> List[str]:
    """
    Extract downloaded file. Handles both single NC file and zip files.
    
    Args:
        zip_or_file_path: Path to the downloaded file
        extract_dir: Directory to extract to (optional)
    
    Returns:
        List of extracted file paths
    """
    # If no extract directory specified, create one based on filename
    if extract_dir is None:
        filename = os.path.basename(zip_or_file_path)
        filename_base = os.path.splitext(filename)[0]
        parent_dir = os.path.dirname(os.path.abspath(zip_or_file_path))
        if not parent_dir:
            parent_dir = "."
        extract_dir = os.path.join(parent_dir, filename_base)
    
    # Create extraction directory if it doesn't exist
    os.makedirs(extract_dir, exist_ok=True)
    
    # Determine file type
    if zip_or_file_path.lower().endswith('.zip'):
        # Zip file extraction
        print(f"Extracting zip file: {zip_or_file_path}")
        with zipfile.ZipFile(zip_or_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = zip_ref.namelist()
            extracted_files = [os.path.join(extract_dir, f) for f in extracted_files]
    elif zip_or_file_path.lower().endswith('.nc'):
        # Single NetCDF file - just copy to extraction directory
        print(f"Copying NetCDF file: {zip_or_file_path}")
        import shutil
        dest_path = os.path.join(extract_dir, os.path.basename(zip_or_file_path))
        shutil.copy(zip_or_file_path, dest_path)
        extracted_files = [dest_path]
    else:
        raise ValueError(f"Unsupported file type: {zip_or_file_path}")
    
    # Find all NetCDF files in the extracted directory
    nc_files = find_netcdf_files(extract_dir)
    
    if not nc_files:
        print(f"Warning: No NetCDF files found in {zip_or_file_path}")
        print(f"Found files: {', '.join(extracted_files)}")
        return extracted_files
    
    print("Extracted NetCDF files:")
    for file in nc_files:
        print(f"  - {file}")
    
    return nc_files

import datetime as dt
from typing import List
import cdsapi

# Instantaneous variables (data_stream-oper_stepType-instant.nc)
instantaneous_vars = [
    # Wind components
    "u10", "v10", "u100", "v100", "u10n", "v10n", "i10fg", "zust",
    
    # Temperature measurements
    "d2m", "t2m", "sst", "skt", "istl1", "istl2", "istl3", "istl4",
    "stl1", "stl2", "stl3", "stl4", "tsn", "lblt", "lict", "ltlt", "lmlt",
    
    # Pressure measurements
    "msl", "sp",
    
    # Cloud variables
    "cbh", "hcc", "lcc", "mcc", "tcc", 
    
    # Water content variables
    "tciw", "tclw", "tcrw", "tcsw", "tcslw", "tcw", "tcwv",
    
    # Surface properties
    "src", "sd", "asn", "rsn", "lsm", "cl", "dl", "licd", "lmld", "lshf",
    
    # Vertical integration variables
    "viiwd", "vilwd", "vigd", "viked", "vimad", "vimdf", "viozd", "vithed", "vited",
    "viiwe", "vilwe", "vige", "vithee", "vikee", "vimae", "vioze", "vitee", "viwve",
    "viec", "vike", "vima", "vimat", "viiwn", "vilwn", "vign", "vithen", "viken",
    "viman", "viozn", "viten", "viwvn", "vipie", "vipile", "vit", "vithe", "vitoe",
    
    # Soil and water variables
    "swvl1", "swvl2", "swvl3", "swvl4", "slt",
    
    # Vegetation variables
    "cvh", "cvl", "lai_hv", "lai_lv", "tvh", "tvl",
    
    # Atmospheric indices
    "cape", "cin", "kx", "totalx",
    
    # Orography variables
    "anor", "isor", "slor", "sdfor", "sdor",
    
    # Albedo variables
    "fal", "alnid", "alnip", "aluvd", "aluvp",
    
    # Surface flux and stress
    "iews", "inss", "ishf",
    
    # Precipitation rates (instantaneous)
    "crr", "csfr", "lsrr", "lssfr", "ptype",
    
    # Other parameters
    "blh", "chnk", "dctb", "deg0l", "flsr", "fsr", "z", "siconc", "tco3",
    "tplb", "tplt", "dndza", "dndzn", "ilspf", "ie"
]

# Accumulated variables (data_stream-oper_stepType-accum.nc)
accumulated_vars = [
    # Precipitation
    "tp", "cp", "csf", "lsp", "lspf", "lsf", "sf",
    
    # Radiation components
    "cdir", "uvb", "ssr", "ssrc", "str", "strc", "ssrdc", "ssrd", "strdc", "strd", 
    "tisr", "tsr", "tsrc", "ttr", "ttrc", "fdir",
    
    # Surface fluxes
    "slhf", "sshf",
    
    # Evaporation and runoff
    "e", "pev", "es", "ro", "sro", "ssro", "smlt",
    
    # Wave and surface stress
    "lgws", "ewss", "mgws", "nsss",
    
    # Dissipation
    "bld", "gwd",
    
    # Other
    "vimd"
]

# Time-averaged variables (data_stream-oper_stepType-avg.nc)
time_averaged_vars = [
    # Averaged precipitation rates
    "avg_cpr", "avg_csfr", "avg_lsprate", "avg_lssfr", "avg_tsrwe", "avg_tprate",
    
    # Averaged fluxes
    "avg_slhtf", "avg_ishf", "avg_ie", "avg_pevr",
    
    # Averaged radiation components
    "avg_sdirswrf", "avg_sdirswrfcs", "avg_sdlwrf", "avg_sdlwrfcs", 
    "avg_sdswrf", "avg_sdswrfcs", "avg_sduvrf", "avg_snlwrf", "avg_snlwrfcs",
    "avg_snswrf", "avg_snswrfcs", "avg_tdswrf", "avg_tnlwrf", "avg_tnlwrfcs",
    "avg_tnswrf", "avg_tnswrfcs",
    
    # Averaged runoff and evaporation
    "avg_rorwe", "avg_esrwe", "avg_smr", "avg_ssurfror", "avg_surfror",
    
    # Averaged stress and dissipation
    "avg_iegwss", "avg_iews", "avg_ingwss", "avg_inss", "avg_ibld", "avg_igwd",
    
    # Other
    "avg_ilspf", "avg_vimdf"
]

# Maximum/minimum variables (data_stream-oper_stepType-max.nc)
maximum_vars = [
    "fg10",        # 10 meter wind gust
    "mx2t",        # Maximum 2 meter temperature
    "mxtpr",       # Maximum total precipitation rate
    "mn2t",        # Minimum 2 meter temperature
    "mntpr"        # Minimum total precipitation rate
]

# Wave-related variables (data_stream-wave_stepType-instant.nc)
wave_vars = [
    # Primary wave parameters
    "mwd", "mwp", "swh", "hmax", "wmb",
    
    # Wave direction parameters
    "mdts", "mdww", "mwd1", "mwd2", "mwd3", "dwi", "wdw", "dwps", "dwww",
    
    # Wave period parameters
    "mpts", "mpww", "mp1", "mp2", "p1ps", "p1ww", "p2ps", "p2ww", 
    "mwp1", "mwp2", "mwp3", "pp1d", "tmax",
    
    # Wave height parameters
    "shts", "shww", "swh1", "swh2", "swh3",
    
    # Wave spectra parameters  
    "wsk", "wsp", "wss", "msqs", "bfi",
    
    # Ocean-atmosphere interaction
    "rhoao", "cdww", "wstar", "phioc", "phiaw", "tauoc", "wind", "ust", "vst"
]

# Map of CDS API variable names to ERA5 netCDF variable names
cds_variable_mapping = {
    # Common CDS API to ERA5 netCDF variable mappings
    "2m_temperature": "t2m",
    "10m_u_component_of_wind": "u10",
    "10m_v_component_of_wind": "v10",
    "surface_pressure": "sp",
    "mean_sea_level_pressure": "msl",
    "2m_dewpoint_temperature": "d2m",
    "skin_temperature": "skt",
    "sea_surface_temperature": "sst",
    "total_precipitation": "tp",
    "10m_wind_gust": "fg10",
    "total_column_water_vapour": "tcwv",
    "total_column_water": "tcw",
    "snow_depth": "sd",
    "snowfall": "sf",
    "surface_latent_heat_flux": "slhf",
    "surface_sensible_heat_flux": "sshf",
    "surface_solar_radiation_downwards": "ssrd",
    "surface_thermal_radiation_downwards": "strd",
    "evaporation": "e",
    "potential_evaporation": "pev",
    "runoff": "ro",
    "soil_temperature_level_1": "stl1",
    "volumetric_soil_water_layer_1": "swvl1",
    "u_component_of_wind_100m": "u100",
    "v_component_of_wind_100m": "v100",
    "significant_height_of_combined_wind_waves_and_swell": "swh",
    "mean_wave_direction": "mwd",
    "mean_wave_period": "mwp"
}


def determine_file_type(variables: List[str]) -> tuple:
    """
    Determine the expected file type based on the requested variables.
    
    Args:
        variables: List of variable names (in CDS API format)
        
    Returns:
        Tuple of (file_extension, variable_group_name)
    """
    # Convert CDS variable names to ERA5 netCDF variable names if needed
    era5_vars = []
    for var in variables:
        if var in cds_variable_mapping:
            era5_vars.append(cds_variable_mapping[var])
        else:
            era5_vars.append(var)
    
    # Check which group(s) the variables belong to
    instant_count = sum(1 for var in era5_vars if var in instantaneous_vars)
    accum_count = sum(1 for var in era5_vars if var in accumulated_vars)
    avg_count = sum(1 for var in era5_vars if var in time_averaged_vars)
    max_count = sum(1 for var in era5_vars if var in maximum_vars)
    wave_count = sum(1 for var in era5_vars if var in wave_vars)
    
    # If all variables are from a single group, return .nc
    if len(era5_vars) == instant_count and instant_count > 0:
        return ".nc", "instantaneous"
    elif len(era5_vars) == accum_count and accum_count > 0:
        return ".nc", "accumulated"
    elif len(era5_vars) == avg_count and avg_count > 0:
        return ".nc", "time-averaged"
    elif len(era5_vars) == max_count and max_count > 0:
        return ".nc", "maximum"
    elif len(era5_vars) == wave_count and wave_count > 0:
        return ".nc", "wave"
    # If variables come from multiple groups, return .zip
    else:
        return ".zip", "mixed"


def download_era5_data(request_id: str, 
                       variables: List[str], 
                       start_date: dt.datetime,
                       end_date: dt.datetime,
                       north: float, 
                       west: float, 
                       south: float, 
                       east: float,
                       resolution: float = 0.1,
                       frequency: str = "hourly") -> str:
    """
    Download ERA5 data with a custom request ID for the filename.
    
    Args:
        request_id: Unique identifier for the request
        variables: List of variables to download
        start_date: Start date for data retrieval (datetime object)
        end_date: End date for data retrieval (datetime object)
        north, west, south, east: Bounding box coordinates
        resolution: Grid resolution for both latitude and longitude (default: 0.1°)
    
    Returns:
        Path to the downloaded file
    """

    frequency = frequency.lower()

    # Choose dataset based on frequency
    if frequency in ["monthly", "yearly"]:
        dataset = "reanalysis-era5-single-levels-monthly-means"
    else:
        dataset = "reanalysis-era5-single-levels"

    # Prepare date ranges
    dates = {}
    current_date = start_date
    while current_date <= end_date:
        year = str(current_date.year)
        if year not in dates:
            dates[year] = {}
        month = str(current_date.month).zfill(2)
        if month not in dates[year]:
            dates[year][month] = []
        dates[year][month].append(str(current_date.day).zfill(2))
        current_date += dt.timedelta(days=1)

    years = list(dates.keys())
    months = []
    days = []
    for year in dates:
        for month in dates[year]:
            if month not in months:
                months.append(month)
            for day in dates[year][month]:
                if day not in days:
                    days.append(day)
    
    # Determine output file extension based on variables
    file_extension, group_type = determine_file_type(variables)
    output_file = f"{request_id}{file_extension}"

    # For monthly means, no need for hours or days
    if frequency in ["monthly", "yearly"]:
        request = {
            "product_type": ["monthly_averaged_reanalysis"],
            "year": years,
            "month": months,
            "time": ["00:00"],
            "variable": variables,
            "area": [north, west, south, east],
            "format": "netcdf",
            "grid": [resolution, resolution],
        }
        # Remove 'day' and 'time' from request
    else:
        hours = [f"{h:02d}:00" for h in range(24)]
        request = {
            "product_type": ["reanalysis"],
            "year": years,
            "month": months,
            "day": days,
            "time": hours,
            "data_format": "netcdf",
            "download_format": "unarchived",
            "variable": variables,
            "area": [north, west, south, east],
            "grid": [resolution, resolution],
        }
    
    print(f"Downloading ERA5 data for request: {request_id}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Area: North: {north}, West: {west}, South: {south}, East: {east}")
    print(f"Variables: {', '.join(variables)}")
    print(f"Variable group: {group_type}")
    print(f"Output format: {file_extension}")
    print(f"Grid Resolution: {resolution}°")
    
    client = cdsapi.Client()
    client.retrieve(dataset, request, output_file)
    
    print(f"Download complete: {output_file}")
    
    return output_file

def filter_netcdf_by_shapefile(ds: xr.Dataset, geojson_data: Dict) -> pd.DataFrame:
    """
    Filter a NetCDF dataset to only include grid points that fall within the GeoJSON polygon
    by first identifying unique lat/lon pairs that are inside the polygon, then filtering the dataset.
    This is much more efficient than converting the entire dataset to DataFrame first.
    """
    print("Starting optimized filtering process...")
    start_time = dt.datetime.now()
    
    # Convert GeoJSON to GeoDataFrame for efficient spatial operations
    if isinstance(geojson_data, dict):
        gdf = gpd.GeoDataFrame.from_features(
            geojson_data["features"] if "features" in geojson_data 
            else [geojson_data]
        )
    else:
        gdf = geojson_data

    # Make sure the CRS is set
    if gdf.crs is None:
        gdf.crs = "EPSG:4326"  # WGS84 - standard for geographic coordinates

    # Create a unified geometry from all polygons in the GeoDataFrame
    unified_polygon = gdf.geometry.union_all()
    
    # Step 1: Extract unique lat/lon coordinates from the NetCDF dataset
    print("→ Extracting unique lat/lon coordinates from dataset...")
    
    # Get the coordinate arrays
    lats = ds.coords['latitude'].values if 'latitude' in ds.coords else ds.coords['lat'].values
    lons = ds.coords['longitude'].values if 'longitude' in ds.coords else ds.coords['lon'].values
    
    # Create all possible lat/lon combinations (grid points)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    unique_coords = pd.DataFrame({
        'latitude': lat_grid.flatten(),
        'longitude': lon_grid.flatten()
    }).drop_duplicates()
    
    total_unique_points = len(unique_coords)
    print(f"✓ Found {total_unique_points} unique lat/lon combinations")
    
    # Step 2: Filter unique coordinates to find which ones are inside the polygon
    print("→ Filtering unique coordinates against polygon...")
    filter_start = dt.datetime.now()
    
    # Create Point geometries for unique coordinates
    unique_coords['geometry'] = [Point(lon, lat) for lon, lat in 
                                zip(unique_coords['longitude'], unique_coords['latitude'])]
    
    # Convert to GeoDataFrame
    gdf_unique_points = gpd.GeoDataFrame(unique_coords, geometry='geometry', crs="EPSG:4326")
    
    # Filter points that are within the polygon
    inside_coords = gdf_unique_points[gdf_unique_points.geometry.within(unified_polygon)].copy()
    
    # Drop the geometry column and keep only lat/lon
    inside_coords = inside_coords[['latitude', 'longitude']].copy()
    
    filter_time = dt.datetime.now() - filter_start
    points_inside_count = len(inside_coords)
    points_outside_count = total_unique_points - points_inside_count
    
    print(f"✓ Coordinate filtering completed in {filter_time.total_seconds():.2f} seconds")
    print(f"  - Points inside: {points_inside_count}")
    print(f"  - Points outside: {points_outside_count}")
    print(f"  - Percentage inside: {points_inside_count/total_unique_points*100:.2f}%")
    
    # Verify we found points inside
    if points_inside_count == 0:
        print("\n!!! WARNING: No points found inside the shapefile !!!")
        print("Possible reasons:")
        print("1. Coordinate system mismatch")
        print("2. Incorrect shapefile")
        print("3. Grid points are outside the shapefile")

        # Additional debugging info
        print(f"\nDataset coordinate ranges:")
        print(f"  Latitude: {lats.min():.4f} to {lats.max():.4f}")
        print(f"  Longitude: {lons.min():.4f} to {lons.max():.4f}")

        # Print shapefile bounds
        print("\nShapefile bounds (west, south, east, north):")
        bounds = unified_polygon.bounds
        if isinstance(bounds, tuple):
            print(f"  {bounds[0]:.4f}, {bounds[1]:.4f}, {bounds[2]:.4f}, {bounds[3]:.4f}")
        else:
            print(f"  {bounds}")

        raise ValueError("No points found inside the specified shapefile")
    
    # Step 3: Use the inside coordinates to filter the original dataset
    print("→ Filtering original dataset using inside coordinates...")
    dataset_filter_start = dt.datetime.now()
    
    # First convert the dataset to DataFrame
    print("  Converting dataset to DataFrame...")
    df = ds.to_dataframe().reset_index()
    original_rows = len(df)
    print(f"  ✓ Converted to DataFrame with {original_rows} rows")
    
    # Create a set of (lat, lon) tuples for fast lookup
    inside_coord_tuples = set(zip(inside_coords['latitude'], inside_coords['longitude']))
    print(f"  ✓ Created lookup set with {len(inside_coord_tuples)} coordinate pairs")
    
    # Filter the DataFrame to keep only rows where (lat, lon) pair is in the inside set
    print("  Filtering DataFrame rows...")
    lat_col = 'latitude' if 'latitude' in df.columns else 'lat'
    lon_col = 'longitude' if 'longitude' in df.columns else 'lon'
    
    # Create a boolean mask for rows where the lat/lon combination is inside
    df['coord_pair'] = list(zip(df[lat_col], df[lon_col]))
    mask = df['coord_pair'].isin(inside_coord_tuples)
    
    # Apply the filter
    filtered_df = df[mask].copy()
    
    # Remove the temporary column
    filtered_df = filtered_df.drop(columns=['coord_pair'])
    
    filtered_rows = len(filtered_df)
    print(f"  ✓ Filtered from {original_rows} to {filtered_rows} rows")
    
    dataset_filter_time = dt.datetime.now() - dataset_filter_start
    print(f"✓ Dataset filtering completed in {dataset_filter_time.total_seconds():.2f} seconds")
    
    end_time = dt.datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print("\n--- Final Filtering Results ---")
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Final DataFrame shape: {filtered_df.shape}")
    print(f"Rows in final dataset: {len(filtered_df)}")
    
    return filtered_df


def get_unique_coordinates_in_polygon(ds: xr.Dataset, geojson_data: Dict) -> pd.DataFrame:
    """
    Alternative helper function that returns just the unique lat/lon pairs inside the polygon.
    This can be useful for other operations or caching coordinate filtering results.
    """
    print("Extracting unique coordinates inside polygon...")
    
    # Convert GeoJSON to GeoDataFrame
    if isinstance(geojson_data, dict):
        gdf = gpd.GeoDataFrame.from_features(
            geojson_data["features"] if "features" in geojson_data 
            else [geojson_data]
        )
    else:
        gdf = geojson_data

    if gdf.crs is None:
        gdf.crs = "EPSG:4326"

    unified_polygon = gdf.geometry.union_all()
    
    # Get coordinate arrays
    lats = ds.coords['latitude'].values if 'latitude' in ds.coords else ds.coords['lat'].values
    lons = ds.coords['longitude'].values if 'longitude' in ds.coords else ds.coords['lon'].values
    
    # Create grid and unique combinations
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    unique_coords = pd.DataFrame({
        'latitude': lat_grid.flatten(),
        'longitude': lon_grid.flatten()
    }).drop_duplicates()
    
    # Filter coordinates
    unique_coords['geometry'] = [Point(lon, lat) for lon, lat in 
                                zip(unique_coords['longitude'], unique_coords['latitude'])]
    gdf_points = gpd.GeoDataFrame(unique_coords, geometry='geometry', crs="EPSG:4326")
    inside_coords = gdf_points[gdf_points.geometry.within(unified_polygon)]
    
    return inside_coords[['latitude', 'longitude']].copy()

def aggregate_by_frequency(df: pd.DataFrame, frequency: str, keep_original_time: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate ERA5 data by the specified frequency for multiple points within a polygon.
    
    The function first aggregates data spatially (across points) for each timestamp,
    then performs temporal aggregation based on the specified frequency.
    
    Parameters:
        df: DataFrame containing ERA5 data with latitude/longitude points and timestamps
        frequency: One of 'hourly', 'daily', 'weekly', 'monthly', 'yearly'
        keep_original_time: Whether to keep the original valid_time column (default: False)
    
    Returns:
        Tuple of (aggregated DataFrame, unique lat/lon DataFrame)
    """
    print(f"Aggregating data to {frequency} frequency...")

    frequency = frequency.lower()
    
    # Store unique lat/lon pairs for reference (not used in aggregation)
    unique_latlongs = df[['latitude', 'longitude']].drop_duplicates().reset_index(drop=True)

    # Ensure time column is properly formatted
    if 'valid_time' in df.columns:
        if not np.issubdtype(df['valid_time'].dtype, np.datetime64):
            df['valid_time'] = pd.to_datetime(df['valid_time'], errors='coerce')
        df['date'] = df['valid_time'].dt.date
        df['hour'] = df['valid_time'].dt.hour
        time_col = 'valid_time'
    else:
        # If no valid_time, assume date and time columns exist
        if 'date' not in df.columns or 'time' not in df.columns:
            print("Warning: No proper time columns found in DataFrame. Skipping aggregation.")
            return df, unique_latlongs
        
        # Convert date and time to datetime if needed
        if not isinstance(df['date'].iloc[0], pd.Timestamp):
            df['date'] = pd.to_datetime(df['date'])
        
        if isinstance(df['time'].iloc[0], str):
            df['hour'] = pd.to_datetime(df['time']).dt.hour
        else:
            df['hour'] = df['time'].apply(lambda t: t.hour)
        
        # Create valid_time column for resampling
        df['valid_time'] = pd.to_datetime(df['date']) + pd.to_timedelta(df['hour'], unit='h')
        time_col = 'valid_time'

    # Define variables by aggregation method
    sum_vars = [
        'tp', 'total_precipitation', 'cp', 'convective_precipitation', 'lsp', 'large_scale_precipitation',
        'sf', 'snowfall', 'csf', 'convective_snowfall', 'lsf', 'large_scale_snowfall',
        'ssr', 'surface_net_solar_radiation', 'str', 'surface_net_thermal_radiation',
        'tsr', 'top_net_solar_radiation', 'ttr', 'top_net_thermal_radiation',
        'ssrd', 'surface_solar_radiation_downward', 'strd', 'surface_thermal_radiation_downward',
        'tisr', 'toa_incident_solar_radiation',
        'slhf', 'surface_latent_heat_flux', 'sshf', 'surface_sensible_heat_flux',
        'ewss', 'eastward_turbulent_surface_stress', 'nsss', 'northward_turbulent_surface_stress',
        'ro', 'runoff', 'sro', 'surface_runoff', 'ssro', 'sub_surface_runoff',
        'e', 'evaporation', 'pev', 'potential_evaporation', 'es', 'snow_evaporation', 'smlt', 'snowmelt',
        'bld', 'boundary_layer_dissipation', 'gwd', 'gravity_wave_dissipation', 'cdir', 'clear_sky_direct_solar_radiation', 
        'uvb', 'downward_uv_radiation', 
        'lgws', 'eastward_gravity_wave_surface_stress',
        'lspf', 'large_scale_precipitation_fraction',
        'mgws', 'meridional_gravity_wave_surface_stress',
        'ssrc', 'surface_net_solar_radiation_clear_sky',
        'strc', 'surface_net_thermal_radiation_clear_sky',
        'ssrdc', 'surface_solar_radiation_downward_clear_sky',
        'strdc', 'surface_thermal_radiation_downward_clear_sky',
        'tsrc', 'top_net_solar_radiation_clear_sky',
        'ttrc', 'top_net_thermal_radiation_clear_sky',
        'fdir', 'total_sky_direct_solar_radiation',
        'vimd', 'vertically_integrated_moisture_divergence'
    ]
    
    # Variables that should use max aggregation
    max_vars = [
        'mx2t', 'maximum_2m_temperature', 'mxtpr', 'maximum_total_precipitation_rate',
        'fg10', '10m_wind_gust', 'hmax', 'maximum_individual_wave_height'
    ]
    
    # Variables that should use min aggregation
    min_vars = [
        'mn2t', 'minimum_2m_temperature', 'mntpr', 'minimum_total_precipitation_rate'
    ]
    
    # Rate variables that should be averaged when temporally aggregating
    rate_vars = [
        'avg_tprate', 'average_total_precipitation_rate',
        'avg_cpr', 'average_convective_precipitation_rate',
        'avg_lsprate', 'average_large_scale_precipitation_rate',
        'avg_sfrate', 'average_snowfall_rate',
        'crr', 'convective_rain_rate',
        'lsrr', 'large_scale_rain_rate',
        'csfr', 'convective_snowfall_rate',
        'lssfr', 'large_scale_snowfall_rate',
        'avg_ibld', 'average_boundary_layer_dissipation',
        'avg_iegwss', 'average_eastward_gravity_wave_surface_stress',
        'avg_iews', 'average_eastward_turbulent_surface_stress',
        'avg_ie', 'average_evaporation_rate',
        'avg_igwd', 'average_gravity_wave_dissipation',
        'avg_ilspf', 'average_large_scale_precipitation_fraction',
        'avg_ingwss', 'average_northward_gravity_wave_surface_stress',
        'avg_inss', 'average_northward_turbulent_surface_stress',
        'avg_pevr', 'average_potential_evaporation_rate',
        'avg_rorwe', 'average_runoff_rate',
        'avg_esrwe', 'average_snow_evaporation_rate',
        'avg_tsrwe', 'average_snowfall_rate',
        'avg_smr', 'average_snowmelt_rate',
        'avg_ssurfror', 'average_sub_surface_runoff_rate',
        'avg_sdirswrf', 'average_surface_direct_shortwave_radiation_flux',
        'avg_sdirswrfcs', 'average_surface_direct_shortwave_radiation_flux_clear_sky',
        'avg_sdlwrf', 'average_surface_downward_long_wave_radiation_flux',
        'avg_sdlwrfcs', 'average_surface_downward_long_wave_radiation_flux_clear_sky',
        'avg_sdswrf', 'average_surface_downward_shortwave_radiation_flux',
        'avg_sdswrfcs', 'average_surface_downward_shortwave_radiation_flux_clear_sky',
        'avg_sduvrf', 'average_surface_downward_uv_radiation_flux',
        'avg_slhtf', 'average_surface_latent_heat_flux',
        'avg_snlwrf', 'average_surface_net_long_wave_radiation_flux',
        'avg_snlwrfcs', 'average_surface_net_long_wave_radiation_flux_clear_sky',
        'avg_snswrf', 'average_surface_net_shortwave_radiation_flux',
        'avg_snswrfcs', 'average_surface_net_shortwave_radiation_flux_clear_sky',
        'avg_surfror', 'average_surface_runoff_rate',
        'avg_ishf', 'average_surface_sensible_heat_flux',
        'avg_tdswrf', 'average_top_downward_shortwave_radiation_flux',
        'avg_tnlwrf', 'average_top_net_long_wave_radiation_flux',
        'avg_tnlwrfcs', 'average_top_net_long_wave_radiation_flux_clear_sky',
        'avg_tnswrf', 'average_top_net_shortwave_radiation_flux',
        'avg_tnswrfcs', 'average_top_net_shortwave_radiation_flux_clear_sky',
        'avg_vimdf', 'average_vertically_integrated_moisture_divergence'
    ]

    # Non-data columns that should be excluded from aggregation
    exclude_cols = {'latitude', 'longitude', 'date', 'time', 'hour', 'expver', 'number', 'valid_time'}
    
    # Improved column matching for different categories
    var_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Match columns that should be summed (more flexible matching)
    sum_cols = []
    for col in var_cols:
        col_lower = col.lower()
        if any(sv == col_lower or sv in col_lower.split('_') for sv in sum_vars):
            sum_cols.append(col)
    
    # Match columns that should use max
    max_cols = []
    for col in var_cols:
        col_lower = col.lower()
        if any(mv == col_lower or mv in col_lower.split('_') for mv in max_vars):
            max_cols.append(col)
    
    # Match columns that should use min
    min_cols = []
    for col in var_cols:
        col_lower = col.lower()
        if any(mv == col_lower or mv in col_lower.split('_') for mv in min_vars):
            min_cols.append(col)
    
    # Match rate columns
    rate_cols = []
    for col in var_cols:
        col_lower = col.lower()
        if any(rv == col_lower or rv in col_lower.split('_') for rv in rate_vars):
            rate_cols.append(col)
    
    # Average columns are those not covered by other aggregation methods
    special_cols = sum_cols + max_cols + min_cols + rate_cols
    avg_cols = [col for col in var_cols if col not in special_cols]

    print(f"Sum columns: {sum_cols}")
    print(f"Max columns: {max_cols}")
    print(f"Min columns: {min_cols}")
    print(f"Rate columns: {rate_cols}")
    print(f"Average columns: {avg_cols}")

    # Return original data if hourly frequency requested
    if frequency == 'hourly':
        # For hourly, just aggregate across spatial points for each hour
        spatial_agg = df.groupby([time_col], as_index=False).agg({
            **{col: 'mean' for col in avg_cols},
            **{col: 'mean' for col in sum_cols},  # Even sum vars are averaged spatially
            **{col: 'max' for col in max_cols},   # Max vars take maximum across points
            **{col: 'min' for col in min_cols},   # Min vars take minimum across points
            **{col: 'mean' for col in rate_cols}  # Rate vars are averaged spatially
        })
        
        # Add standardized date columns for hourly frequency
        spatial_agg['date'] = spatial_agg[time_col].dt.date
        spatial_agg['year'] = spatial_agg[time_col].dt.year
        spatial_agg['month'] = spatial_agg[time_col].dt.month
        spatial_agg['day'] = spatial_agg[time_col].dt.day
        spatial_agg['hour'] = spatial_agg[time_col].dt.hour
        
        # Drop the original time column if requested
        if not keep_original_time:
            spatial_agg = spatial_agg.drop(columns=[time_col])
            
        return spatial_agg, unique_latlongs

    # Define frequency mapping for pandas resampling
    freq_map = {
        'daily': 'D',    # Calendar day
        'weekly': 'W',   # Weekly
        'monthly': 'MS', # Month start
        'yearly': 'AS'   # Year start
    }
    
    if frequency not in freq_map and frequency != 'hourly':
        raise ValueError(f"Invalid frequency: {frequency}. Must be one of {list(freq_map.keys()) + ['hourly']}")
    
    # Step 1: First spatial aggregation - aggregate across points for each timestamp
    # Different aggregation methods based on variable type
    spatial_agg = df.groupby([time_col], as_index=False).agg({
        **{col: 'mean' for col in avg_cols},
        **{col: 'mean' for col in sum_cols},  # Even sum vars are averaged spatially
        **{col: 'max' for col in max_cols},   # Max vars take maximum across points
        **{col: 'min' for col in min_cols},   # Min vars take minimum across points
        **{col: 'mean' for col in rate_cols}  # Rate vars are averaged spatially
    })
    
    # Step 2: Temporal aggregation based on the specified frequency
    # Set the datetime as index for resampling
    spatial_agg = spatial_agg.set_index(time_col)
    
    # Perform temporal aggregation
    result = pd.DataFrame()
    
    # For sum variables, sum over time periods
    for col in sum_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).sum()
    
    # For max variables, take maximum over time periods
    for col in max_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).max()
    
    # For min variables, take minimum over time periods
    for col in min_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).min()
    
    # For rate variables, average over time periods (they're already rates)
    for col in rate_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).mean()
    
    # For average variables, average over time periods
    for col in avg_cols:
        if col in spatial_agg.columns:
            result[col] = spatial_agg[col].resample(freq_map[frequency]).mean()
    
    # Reset index to get the datetime as a column
    result = result.reset_index()
    
    # Create standardized date columns based on frequency
    result['year'] = result[time_col].dt.year
    
    if frequency == 'daily':
        result['month'] = result[time_col].dt.month
        result['day'] = result[time_col].dt.day
        result['date'] = result[time_col].dt.date
    elif frequency == 'weekly':
        result['week'] = result[time_col].dt.isocalendar().week
    elif frequency == 'monthly':
        result['month'] = result[time_col].dt.month
    
    # Drop the original time column if requested
    if not keep_original_time:
        result = result.drop(columns=[time_col])
    
    return result, unique_latlongs

def process_era5_data(request_id: str, 
                      variables: List[str], 
                      start_date: dt.datetime,
                      end_date: dt.datetime,
                      geojson_file: str,
                      frequency: str = 'hourly',
                      resolution: float = 0.25) -> pd.DataFrame:
    """
    Complete workflow for downloading and processing ERA5 data with time range support.
    Automatically chunks large time range requests for efficient processing.
    
    Args:
        request_id: Unique identifier for the request
        variables: List of variables to download
        start_date: Start date for data retrieval (datetime object)
        end_date: End date for data retrieval (datetime object)
        geojson_file: Path to the GeoJSON file
        frequency: Aggregation frequency ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        resolution: Grid resolution in degrees (default: 0.25°)
    
    Returns:
        Filtered and aggregated DataFrame with the processed data
    """
    print(f"\n{'='*60}")
    print(f"STARTING ERA5 DATA PROCESSING")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    print(f"Variables: {variables}")
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Frequency: {frequency}")
    print(f"Resolution: {resolution}°")
    print(f"GeoJSON File: {geojson_file}")
    
    # Validate inputs
    print("\n--- Input Validation ---")
    if not variables:
        raise ValueError("Variables list cannot be empty")
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")
    if not os.path.exists(geojson_file):
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_file}")
    print("✓ All inputs validated successfully")
    
    # Load GeoJSON file with encoding handling
    print("\n--- Loading GeoJSON File ---")
    try:
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        geojson_data = None
        
        print(f"Attempting to load: {geojson_file}")
        for i, encoding in enumerate(encodings, 1):
            try:
                print(f"  Trying encoding {i}/{len(encodings)}: {encoding}")
                with open(geojson_file, 'r', encoding=encoding) as f:
                    geojson_data = json.load(f)
                print(f"✓ Successfully loaded GeoJSON file with {encoding} encoding")
                break
            except UnicodeDecodeError as e:
                print(f"  ✗ Failed with {encoding}: {str(e)[:50]}...")
                continue
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON decode error with {encoding}: {str(e)[:50]}...")
                continue
        
        if geojson_data is None:
            raise ValueError(f"Could not load {geojson_file} as valid JSON with any common encoding")
            
        # Validate GeoJSON structure
        if 'features' not in geojson_data:
            print("Warning: GeoJSON doesn't have 'features' key, attempting to process anyway")
        else:
            print(f"✓ GeoJSON contains {len(geojson_data['features'])} feature(s)")
            
    except Exception as e:
        print(f"✗ Error loading GeoJSON file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get bounding box coordinates
    print("\n--- Calculating Bounding Box ---")
    try:
        west, south, east, north = get_bounding_box(geojson_data)
        print(f"✓ Bounding Box calculated:")
        print(f"  North: {north:.4f}°")
        print(f"  South: {south:.4f}°")
        print(f"  East:  {east:.4f}°")
        print(f"  West:  {west:.4f}°")
        print(f"  Area:  {abs(east-west):.4f}° × {abs(north-south):.4f}°")
    except Exception as e:
        print(f"✗ Error calculating bounding box: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Determine processing strategy
    print("\n--- Determining Processing Strategy ---")
    use_monthly = frequency in ["monthly", "yearly"]
    print(f"Using monthly dataset: {use_monthly}")
    
    if use_monthly:
        max_months_per_chunk = 10
        total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        needs_chunking = total_months > max_months_per_chunk
        print(f"Total months to process: {total_months}")
        print(f"Max months per chunk: {max_months_per_chunk}")
        print(f"Needs chunking: {needs_chunking}")
    else:
        max_days_per_chunk = 14
        total_days = (end_date - start_date).days + 1
        needs_chunking = total_days > max_days_per_chunk
        print(f"Total days to process: {total_days}")
        print(f"Max days per chunk: {max_days_per_chunk}")
        print(f"Needs chunking: {needs_chunking}")

    all_filtered_data = []
    processing_start_time = time.time()

    if needs_chunking and use_monthly:
        # --- Case 1: Needs chunking, needs monthly dataset ---
        current_date = start_date
        chunk_number = 1
        total_chunks = math.ceil(total_months / max_months_per_chunk)
        print(f"Will process {total_chunks} chunks C1")
        
        while current_date <= end_date:
            chunk_start_time = time.time()
            print(f"\n{'='*50}")
            print(f"CHUNK {chunk_number}/{total_chunks}")
            print(f"{'='*50}")
            
            # Calculate chunk end date (last day of the chunk)
            chunk_end_year = current_date.year + ((current_date.month - 1 + max_months_per_chunk - 1) // 12)
            chunk_end_month = ((current_date.month - 1 + max_months_per_chunk - 1) % 12) + 1
            # Last day of chunk_end_month
            next_month = dt.datetime(chunk_end_year, chunk_end_month, 28) + dt.timedelta(days=4)
            last_day = next_month - dt.timedelta(days=next_month.day)
            chunk_end = min(last_day, end_date)
            
            print(f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
            
            try:
                print("  → Downloading ERA5 data...")
                download_file = download_era5_data(
                    f"{request_id}_chunk{chunk_number}", variables, current_date, chunk_end,
                    north, west, south, east, resolution, frequency
                )
                print(f"  ✓ Download completed: {download_file}")
                
                print("  → Extracting files...")
                nc_files = extract_download(download_file)
                print(f"  ✓ Extracted {len(nc_files)} files")
                
                chunk_datasets = []
                print("  → Processing NetCDF files...")
                for i, nc_file in enumerate(nc_files, 1):
                    if not nc_file.lower().endswith('.nc'):
                        print(f"    Skipping non-NetCDF file: {nc_file}")
                        continue
                    try:
                        print(f"    Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}")
                        ds = xr.open_dataset(nc_file)
                        chunk_datasets.append(ds)
                        print(f"    ✓ Loaded dataset with shape: {dict(ds.dims)}")
                    except Exception as e:
                        print(f"    ✗ Error processing {nc_file}: {e}", file=sys.stderr)
                        
                if not chunk_datasets:
                    print("  ✗ No datasets were successfully processed for this chunk")
                    chunk_number += 1
                    next_month = chunk_end + dt.timedelta(days=1)
                    current_date = next_month
                    continue
                
                print("  → Merging datasets...")
                merged_chunk_ds = xr.merge(chunk_datasets) if len(chunk_datasets) > 1 else chunk_datasets[0]
                print(f"  ✓ Merged dataset shape: {dict(merged_chunk_ds.dims)}")
                
                print("  → Filtering by shapefile...")
                filtered_chunk_df = filter_netcdf_by_shapefile(merged_chunk_ds, geojson_data)
                print(f"  ✓ Filtered data shape: {filtered_chunk_df.shape}")
                
                all_filtered_data.append(filtered_chunk_df)
                
                chunk_time = time.time() - chunk_start_time
                print(f"  ✓ Chunk completed in {chunk_time:.2f} seconds")
                
            except Exception as e:
                print(f"  ✗ Error processing chunk {chunk_number}: {e}", file=sys.stderr)
                # Continue with next chunk instead of failing completely
                
            chunk_number += 1
            next_month = chunk_end + dt.timedelta(days=1)
            current_date = next_month
            
            if chunk_number <= total_chunks:
                print("  → Waiting 5 seconds before next chunk...")
                time.sleep(5)
        
        if not all_filtered_data:
            print("✗ No data was successfully processed from any chunk", file=sys.stderr)
            sys.exit(1)
            
        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"✓ Combined data shape: {filtered_df.shape}")
        
        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(subset=['valid_time', 'latitude', 'longitude'])
        removed_duplicates = initial_rows - len(filtered_df)
        
    elif needs_chunking and not use_monthly:
        # --- Case 2: Needs chunking, does NOT need monthly dataset ---
        current_date = start_date
        chunk_number = 1
        total_chunks = math.ceil(total_days / max_days_per_chunk)
        print(f"Will process {total_chunks} chunks C2")
        
        while current_date <= end_date:
            chunk_start_time = time.time()
            print(f"\n{'='*50}")
            print(f"CHUNK {chunk_number}/{total_chunks}")
            print(f"{'='*50}")
            
            chunk_end = min(current_date + dt.timedelta(days=max_days_per_chunk-1), end_date)
            print(f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
            
            try:
                print("  → Downloading ERA5 data...")
                download_file = download_era5_data(
                    f"{request_id}_chunk{chunk_number}", variables, current_date, chunk_end,
                    north, west, south, east, resolution, frequency
                )
                print(f"  ✓ Download completed: {download_file}")
                
                print("  → Extracting files...")
                nc_files = extract_download(download_file)
                print(f"  ✓ Extracted {len(nc_files)} files")
                
                chunk_datasets = []
                print("  → Processing NetCDF files...")
                for i, nc_file in enumerate(nc_files, 1):
                    if not nc_file.lower().endswith('.nc'):
                        print(f"    Skipping non-NetCDF file: {nc_file}")
                        continue
                    try:
                        print(f"    Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}")
                        ds = xr.open_dataset(nc_file)
                        chunk_datasets.append(ds)
                        print(f"    ✓ Loaded dataset with shape: {dict(ds.dims)}")
                    except Exception as e:
                        print(f"    ✗ Error processing {nc_file}: {e}", file=sys.stderr)
                        
                if not chunk_datasets:
                    print("  ✗ No datasets were successfully processed for this chunk")
                    chunk_number += 1
                    current_date = chunk_end + dt.timedelta(days=1)
                    continue
                
                print("  → Merging datasets...")
                merged_chunk_ds = xr.merge(chunk_datasets) if len(chunk_datasets) > 1 else chunk_datasets[0]
                print(f"  ✓ Merged dataset shape: {dict(merged_chunk_ds.dims)}")
                
                print("  → Filtering by shapefile...")
                filtered_chunk_df = filter_netcdf_by_shapefile(merged_chunk_ds, geojson_data)
                print(f"  ✓ Filtered data shape: {filtered_chunk_df.shape}")
                
                all_filtered_data.append(filtered_chunk_df)
                
                chunk_time = time.time() - chunk_start_time
                print(f"  ✓ Chunk completed in {chunk_time:.2f} seconds")
                
            except Exception as e:
                print(f"  ✗ Error processing chunk {chunk_number}: {e}", file=sys.stderr)
                # Continue with next chunk instead of failing completely
                
            chunk_number += 1
            current_date = chunk_end + dt.timedelta(days=1)
            
            if chunk_number <= total_chunks:
                print("  → Waiting 5 seconds before next chunk...")
                time.sleep(5)
        
        if not all_filtered_data:
            print("✗ No data was successfully processed from any chunk", file=sys.stderr)
            sys.exit(1)
            
        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"✓ Combined data shape: {filtered_df.shape}")
        
        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(subset=['valid_time', 'latitude', 'longitude'])
        removed_duplicates = initial_rows - len(filtered_df)
        
    elif not needs_chunking and use_monthly:
        # --- Case 3: Does NOT need chunking, needs monthly dataset ---
        print(f"Processing as a single chunk ({total_months} months)... C3")
        
        try:
            print("→ Downloading ERA5 data...")
            download_file = download_era5_data(
                request_id, variables, start_date, end_date,
                north, west, south, east, resolution, frequency
            )
            print(f"✓ Download completed: {download_file}")
            
            print("→ Extracting files...")
            nc_files = extract_download(download_file)
            print(f"✓ Extracted {len(nc_files)} files")
            
            all_datasets = []
            print("→ Processing NetCDF files...")
            for i, nc_file in enumerate(nc_files, 1):
                if not nc_file.lower().endswith('.nc'):
                    print(f"  Skipping non-NetCDF file: {nc_file}")
                    continue
                try:
                    print(f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}")
                    ds = xr.open_dataset(nc_file)
                    all_datasets.append(ds)
                    print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")
                except Exception as e:
                    print(f"  ✗ Error processing {nc_file}: {e}", file=sys.stderr)
                    
            if not all_datasets:
                print("✗ No datasets were successfully processed", file=sys.stderr)
                sys.exit(1)
            
            print("→ Merging datasets...")
            merged_ds = xr.merge(all_datasets) if len(all_datasets) > 1 else all_datasets[0]
            print(f"✓ Merged dataset shape: {dict(merged_ds.dims)}")
            
            print("→ Filtering by shapefile...")
            filtered_df = filter_netcdf_by_shapefile(merged_ds, geojson_data)
            print(f"✓ Filtered data shape: {filtered_df.shape}")
            
            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(subset=['valid_time', 'latitude', 'longitude'])
            removed_duplicates = initial_rows - len(filtered_df)
            
        except Exception as e:
            print(f"✗ Error in single monthly processing: {e}", file=sys.stderr)
            sys.exit(1)
            
    else:
        # --- Case 4: Does NOT need chunking, does NOT need monthly dataset ---
        print(f"Processing as a single chunk ({total_days} days)... C4")
        
        try:
            print("→ Downloading ERA5 data...")
            download_file = download_era5_data(
                request_id, variables, start_date, end_date,
                north, west, south, east, resolution, frequency
            )
            print(f"✓ Download completed: {download_file}")
            
            print("→ Extracting files...")
            nc_files = extract_download(download_file)
            print(f"✓ Extracted {len(nc_files)} files")
            
            all_datasets = []
            print("→ Processing NetCDF files...")
            for i, nc_file in enumerate(nc_files, 1):
                if not nc_file.lower().endswith('.nc'):
                    print(f"  Skipping non-NetCDF file: {nc_file}")
                    continue
                try:
                    print(f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}")
                    ds = xr.open_dataset(nc_file)
                    all_datasets.append(ds)
                    print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")
                except Exception as e:
                    print(f"  ✗ Error processing {nc_file}: {e}", file=sys.stderr)
                    
            if not all_datasets:
                print("✗ No datasets were successfully processed", file=sys.stderr)
                sys.exit(1)
            
            print("→ Merging datasets...")
            merged_ds = xr.merge(all_datasets) if len(all_datasets) > 1 else all_datasets[0]
            print(f"✓ Merged dataset shape: {dict(merged_ds.dims)}")
            
            print("→ Filtering by shapefile...")
            filtered_df = filter_netcdf_by_shapefile(merged_ds, geojson_data)
            print(f"✓ Filtered data shape: {filtered_df.shape}")
            
            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(subset=['valid_time', 'latitude', 'longitude'])
            removed_duplicates = initial_rows - len(filtered_df)
            
        except Exception as e:
            print(f"✗ Error in single daily processing: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Aggregate by frequency (same for all cases)
    print(f"\n--- Temporal Aggregation ({frequency}) ---")
    try:
        print("→ Performing temporal aggregation...")
        aggregation_start_time = time.time()
        (aggregated_df, unique_latlongs) = aggregate_by_frequency(filtered_df, frequency)
        aggregation_time = time.time() - aggregation_start_time
        print(f"✓ Aggregation completed in {aggregation_time:.2f} seconds")
        print(f"✓ Aggregated data shape: {aggregated_df.shape}")
        print(f"✓ Unique lat/long combinations: {len(unique_latlongs)}")
    except Exception as e:
        print(f"✗ Error during aggregation: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Save processed data
    print(f"\n--- Saving Results ---")
    try:
        output_dir = f"{request_id}_output"
        os.makedirs(output_dir, exist_ok=True)
        print(f"→ Created output directory: {output_dir}")
        
        # Save aggregated data to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_{frequency}_data.csv")
        aggregated_df.to_csv(csv_output, index=False)
        print(f"✓ Aggregated data exported to: {csv_output}")
        
        # Save unique lat/longs to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_unique_latlongs.csv")
        unique_latlongs.to_csv(csv_output, index=False)
        print(f"✓ Unique lat/longs exported to: {csv_output}")

        # Save raw data to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_raw_data.csv")
        filtered_df.to_csv(csv_output, index=False)
        print(f"✓ Raw data exported to: {csv_output}")
        
    except Exception as e:
        print(f"✗ Error saving results: {e}", file=sys.stderr)
        # Don't exit here as we still want to return the data

    # Calculate and display summary statistics
    print(f"\n--- Summary Statistics ---")
    try:
        total_processing_time = time.time() - processing_start_time
        print(f"Total processing time: {total_processing_time:.2f} seconds")
        print(f"Final dataset shape: {aggregated_df.shape}")
        
        print("\nFirst 5 rows of aggregated data:")
        print(aggregated_df.head())
        
        print(f"\n{'='*60}")
        print(f"ERA5 DATA PROCESSING COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Warning: Error generating summary statistics: {e}", file=sys.stderr)
    
    return aggregated_df

import json
import os
import datetime as dt
from typing import List, Dict, Any, Union
import pandas as pd
import tempfile

def load_json_with_encoding(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file with appropriate encoding detection.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data as a dictionary
        
    Raises:
        ValueError: If the file cannot be parsed as JSON with any encoding
    """
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
                print(f"Successfully loaded JSON file with {encoding} encoding")
                return data
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError:
            continue
        except Exception as e:
            continue
    
    # If we get here, none of the encodings worked
    raise ValueError(f"Could not load {file_path} as valid JSON with any common encoding")


def is_valid_geojson(json_data: Dict[str, Any]) -> bool:
    """
    Check if the provided JSON data is valid GeoJSON.
    
    Args:
        json_data: Parsed JSON data
        
    Returns:
        True if it's valid GeoJSON, False otherwise
    """
    # Check if it's a dictionary
    if not isinstance(json_data, dict):
        return False
    
    # Basic GeoJSON structure check
    if 'type' not in json_data:
        return False
    
    # Valid GeoJSON types
    valid_types = ['FeatureCollection', 'Feature', 'Point', 'MultiPoint', 
                   'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon', 
                   'GeometryCollection']
    
    if json_data['type'] not in valid_types:
        return False
    
    # More specific checks based on type
    if json_data['type'] == 'FeatureCollection':
        return 'features' in json_data and isinstance(json_data['features'], list)
    
    elif json_data['type'] == 'Feature':
        return 'geometry' in json_data and isinstance(json_data['geometry'], dict)
    
    # For geometry types, check for coordinates
    elif json_data['type'] in ['Point', 'MultiPoint', 'LineString', 'MultiLineString', 
                             'Polygon', 'MultiPolygon']:
        return 'coordinates' in json_data
    
    # For GeometryCollection
    elif json_data['type'] == 'GeometryCollection':
        return 'geometries' in json_data and isinstance(json_data['geometries'], list)
    
    return False


def convert_to_geojson(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert various JSON formats to valid GeoJSON.
    
    This function tries to intelligently convert different JSON structures
    to proper GeoJSON format based on the content.
    
    Args:
        json_data: The parsed JSON data
        
    Returns:
        A valid GeoJSON dictionary
        
    Raises:
        ValueError: If the JSON cannot be converted to GeoJSON
    """
    # Case 1: It's already GeoJSON but failed validation due to minor issues
    if 'type' in json_data:
        if json_data['type'] in ['Feature', 'FeatureCollection']:
            # Try to fix common issues
            if json_data['type'] == 'FeatureCollection' and 'features' not in json_data:
                json_data['features'] = []
                
            if json_data['type'] == 'Feature' and 'geometry' not in json_data:
                raise ValueError("Feature missing geometry and cannot be automatically fixed")
                
            return json_data
    
    # Case 2: It contains coordinates or a bounding box directly
    if 'coordinates' in json_data:
        # Assume it's meant to be a Polygon
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': json_data['coordinates']
            },
            'properties': {}
        }
    
    # Case 3: It contains a bounding box specified as [west, south, east, north]
    if 'bbox' in json_data and isinstance(json_data['bbox'], list) and len(json_data['bbox']) >= 4:
        west, south, east, north = json_data['bbox'][0:4]
        return create_geojson_from_bbox(west, south, east, north)
    
    # Case 4: It contains explicit lat/lon boundaries
    keys = [k.lower() for k in json_data.keys()]
    if all(k in keys for k in ['north', 'south', 'east', 'west']):
        idx = {k: keys.index(k) for k in ['north', 'south', 'east', 'west']}
        actual_keys = list(json_data.keys())
        north = json_data[actual_keys[idx['north']]]
        south = json_data[actual_keys[idx['south']]]
        east = json_data[actual_keys[idx['east']]]
        west = json_data[actual_keys[idx['west']]]
        return create_geojson_from_bbox(west, south, east, north)
    
    # If we've gotten here, we can't automatically convert it
    raise ValueError("Cannot automatically convert the provided JSON to GeoJSON format")


def create_geojson_from_bbox(west: float, south: float, east: float, north: float) -> Dict[str, Any]:
    """
    Create a GeoJSON polygon from bounding box coordinates.
    
    Args:
        west: Western longitude
        south: Southern latitude
        east: Eastern longitude
        north: Northern latitude
        
    Returns:
        A GeoJSON Feature with a Polygon geometry
    """
    # Create a polygon from the bounding box
    coordinates = [
        [
            [west, south],  # Bottom-left
            [east, south],  # Bottom-right
            [east, north],  # Top-right
            [west, north],  # Top-left
            [west, south]   # Close the polygon
        ]
    ]
    
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': coordinates
        },
        'properties': {
            'description': f'Bounding box: N:{north}, W:{west}, S:{south}, E:{east}'
        }
    }


def create_temp_geojson(geojson_data: Dict[str, Any], request_id: str) -> str:
    """
    Create a temporary GeoJSON file with the provided data.
    
    Args:
        geojson_data: Valid GeoJSON data
        request_id: Unique identifier for the request (used in filename)
        
    Returns:
        Path to the created temporary file
    """
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"{request_id}_temp_geojson.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2)
    
    return output_path

def era5ify(
    request_id: str, 
    variables: List[str], 
    start_date: dt.datetime,
    end_date: dt.datetime,
    json_file: str,
    frequency: str = 'hourly',
    resolution: float = 0.25
) -> pd.DataFrame:
    """
    Wrapper function that handles different JSON formats before passing to process_era5_data.
    
    Args:
        request_id: Unique identifier for the request
        variables: List of variables to download
        start_date: Start date for data retrieval (datetime object)
        end_date: End date for data retrieval (datetime object)
        json_file: Path to the JSON or GeoJSON file
        frequency: Aggregation frequency ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        resolution: Grid resolution in degrees (default: 0.25°)
    
    Returns:
        Filtered and aggregated DataFrame with the processed data
    """
    # Handle different file encodings
    json_data = load_json_with_encoding(json_file)
    
    # Check if it's valid GeoJSON
    if is_valid_geojson(json_data):
        print(f"Valid GeoJSON detected: {json_file}")
        # Use the original file directly since it's already valid GeoJSON
        return process_era5_data(request_id, variables, start_date, end_date, 
                                json_file, frequency, resolution)
    else:
        print(f"Converting JSON to GeoJSON format...")
        # Convert to GeoJSON and save to a temporary file
        geojson_data = convert_to_geojson(json_data)
        temp_geojson_file = create_temp_geojson(geojson_data, request_id)
        print(f"Created temporary GeoJSON file: {temp_geojson_file}")
        
        try:
            # Process with the converted GeoJSON
            return process_era5_data(request_id, variables, start_date, end_date, 
                                    temp_geojson_file, frequency, resolution)
        finally:
            # Clean up temporary file after processing
            if os.path.exists(temp_geojson_file):
                print(f"Removing temporary GeoJSON file: {temp_geojson_file}")
                os.remove(temp_geojson_file)