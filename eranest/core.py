import os
import sys
import json
from calendar import monthrange
import xarray as xr
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
import datetime as dt
import math
import glob
import tempfile
import shutil
import time
from shapely.geometry import shape, Polygon, MultiPolygon, Point
from dataclasses import dataclass
try:
    from .config import ensure_cdsapi_config  # Package-style
except ImportError:
    from config import ensure_cdsapi_config   # Notebook/script-style

from .download import download_era5_single_lvl, download_era5_pressure_lvl
from .processing import (
    aggregate_by_frequency,
    aggregate_pressure_levels,
    filter_netcdf_by_shapefile,
    get_unique_coordinates_in_polygon,
    extract_download,
    find_netcdf_files
)
from .util import (
    extract_coords_from_geometry,
    get_bounding_box,
    load_json_with_encoding,
    is_valid_geojson,
    convert_to_geojson,
    create_geojson_from_bbox,
    create_temp_geojson,
    Colors
)

SUM_VARS = [
    "tp",
    "total_precipitation",
    "cp",
    "convective_precipitation",
    "lsp",
    "large_scale_precipitation",
    "sf",
    "snowfall",
    "csf",
    "convective_snowfall",
    "lsf",
    "large_scale_snowfall",
    "ssr",
    "surface_net_solar_radiation",
    "str",
    "surface_net_thermal_radiation",
    "tsr",
    "top_net_solar_radiation",
    "ttr",
    "top_net_thermal_radiation",
    "ssrd",
    "surface_solar_radiation_downward",
    "strd",
    "surface_thermal_radiation_downward",
    "tisr",
    "toa_incident_solar_radiation",
    "slhf",
    "surface_latent_heat_flux",
    "sshf",
    "surface_sensible_heat_flux",
    "ewss",
    "eastward_turbulent_surface_stress",
    "nsss",
    "northward_turbulent_surface_stress",
    "ro",
    "runoff",
    "sro",
    "surface_runoff",
    "ssro",
    "sub_surface_runoff",
    "e",
    "evaporation",
    "pev",
    "potential_evaporation",
    "es",
    "snow_evaporation",
    "smlt",
    "snowmelt",
    "bld",
    "boundary_layer_dissipation",
    "gwd",
    "gravity_wave_dissipation",
    "cdir",
    "clear_sky_direct_solar_radiation",
    "uvb",
    "downward_uv_radiation",
    "lgws",
    "eastward_gravity_wave_surface_stress",
    "lspf",
    "large_scale_precipitation_fraction",
    "mgws",
    "meridional_gravity_wave_surface_stress",
    "ssrc",
    "surface_net_solar_radiation_clear_sky",
    "strc",
    "surface_net_thermal_radiation_clear_sky",
    "ssrdc",
    "surface_solar_radiation_downward_clear_sky",
    "strdc",
    "surface_thermal_radiation_downward_clear_sky",
    "tsrc",
    "top_net_solar_radiation_clear_sky",
    "ttrc",
    "top_net_thermal_radiation_clear_sky",
    "fdir",
    "total_sky_direct_solar_radiation",
    "vimd",
    "vertically_integrated_moisture_divergence",
]

@dataclass
class ProcessingParams:
    request_id: str
    variables: List[str]
    start_date: dt.datetime
    end_date: dt.datetime
    frequency: str = "hourly"
    resolution: float = 0.25
    pressure_levels: Optional[List[str]] = None
    north: Optional[float] = None
    south: Optional[float] = None
    east: Optional[float] = None
    west: Optional[float] = None
    geojson_file: Optional[str] = None
    geojson_data: Optional[Dict] = None

def download_with_retry(download_func, params: ProcessingParams, chunk_id: Optional[str] = None):
    """Generic download function with retry logic"""
    max_retries = 5
    retry_delay = 30
    
    download_args = {
        'request_id': chunk_id or params.request_id,
        'variables': params.variables,
        'start_date': params.start_date,
        'end_date': params.end_date,
        'north': params.north,
        'west': params.west,
        'south': params.south,
        'east': params.east,
        'resolution': params.resolution,
        'frequency': params.frequency
    }
    
    if download_func == download_era5_pressure_lvl:
        download_args['pressure_levels'] = params.pressure_levels

    for attempt in range(max_retries + 1):
        try:
            print(f"  → Downloading ERA5 data (attempt {attempt + 1}/{max_retries + 1})...")
            download_file = download_func(**download_args)
            print(f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")
            return download_file
        except Exception as e:
            error_msg = str(e)
            print(f"  {Colors.RED}✗ Download attempt {attempt + 1} failed: {error_msg}{Colors.RESET}")
            
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                print(f"  {Colors.RED}✗ All {max_retries + 1} download attempts failed{Colors.RESET}")
                raise e

def process_time_chunks(params: ProcessingParams, download_func, process_func):
    """Handle time-based chunking of downloads and processing"""
    use_monthly = params.frequency in ["monthly", "yearly"]
    
    if use_monthly:
        max_per_chunk = 100  # months
        total_units = (params.end_date.year - params.start_date.year) * 12 + (params.end_date.month - params.start_date.month) + 1
    else:
        max_per_chunk = 14  # days
        total_units = (params.end_date - params.start_date).days + 1
    
    needs_chunking = total_units > max_per_chunk
    all_data = []
    
    if not needs_chunking:
        return process_func(params)
    
    # Chunked processing
    current_date = params.start_date
    chunk_number = 1
    total_chunks = math.ceil(total_units / max_per_chunk)
    
    while current_date <= params.end_date:
        chunk_params = ProcessingParams(**params.__dict__)
        
        # Calculate chunk dates
        if use_monthly:
            chunk_end_year = current_date.year + ((current_date.month - 1 + max_per_chunk - 1) // 12)
            chunk_end_month = ((current_date.month - 1 + max_per_chunk - 1) % 12) + 1
            next_month = dt.datetime(chunk_end_year, chunk_end_month, 28) + dt.timedelta(days=4)
            chunk_end = min(next_month - dt.timedelta(days=next_month.day), params.end_date)
        else:
            chunk_end = min(current_date + dt.timedelta(days=max_per_chunk - 1), params.end_date)
        
        chunk_msg = (
            f"{Colors.CYAN}PROCESSING CHUNK {chunk_number}/{total_chunks}{Colors.RESET}\n"
            f"Date Range: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}\n"
            f"Variables:  {', '.join(params.variables)}"
        )
        if params.pressure_levels:
            chunk_msg += f"\nLevels:     {', '.join(params.pressure_levels)}"
        print(chunk_msg)

        chunk_params.start_date = current_date
        chunk_params.end_date = chunk_end
        
        try:
            start_time = time.time()
            chunk_data = process_func(chunk_params, chunk_number, total_chunks)
            elapsed = time.time() - start_time
            print(f"{Colors.GREEN}✓ Chunk completed in {elapsed:.1f} seconds{Colors.RESET}")
            all_data.append(chunk_data)
        except Exception as e:
            print(f"  {Colors.RED}✗ Error processing chunk {chunk_number}: {e}{Colors.RESET}")
        
        # Prepare for next chunk
        chunk_number += 1
        current_date = chunk_end + dt.timedelta(days=1)
        
        if chunk_number <= total_chunks:
            time.sleep(10)  # Rate limiting
    
    if not all_data:
        raise ValueError("No data was successfully processed from any chunk")
    
    return pd.concat(all_data, ignore_index=True)

def process_era5_data(params: ProcessingParams, chunk_info: Optional[Tuple[int, int]] = None):
    """Core processing function for both single and pressure level data"""
    chunk_number, total_chunks = chunk_info or (1, 1)
    
    # Determine download function
    download_func = (download_era5_pressure_lvl if params.pressure_levels 
                    else download_era5_single_lvl)
    
    # Download data
    chunk_id = f"{params.request_id}_chunk{chunk_number}" if total_chunks > 1 else params.request_id
    download_file = download_with_retry(download_func, params, chunk_id)
    
    # Process downloaded files
    nc_files = extract_download(download_file)
    datasets = []

    print(f"\nProcessing downloaded data:")
    print(f"- Found {len(nc_files)} file(s)")
    
    for i, nc_file in enumerate(nc_files, 1):
        if not nc_file.lower().endswith(".nc"):
            continue
        print(f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}")
        try:
            ds = xr.open_dataset(nc_file)
            print(f"  ✓ Loaded: Dimensions: {ds.sizes}")
            datasets.append(ds)
        except Exception as e:
            print(f"    {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}")
    
    if not datasets:
        raise ValueError("No valid datasets were processed")
    
    # Merge and convert to DataFrame
    merged_ds = xr.merge(datasets) if len(datasets) > 1 else datasets[0]
    
    # Apply filtering if GeoJSON provided
    if params.geojson_data:
        df = filter_netcdf_by_shapefile(merged_ds, params.geojson_data)
    else:
        df = merged_ds.to_dataframe().reset_index()
    
    # Remove duplicates
    dup_cols = ["valid_time", "latitude", "longitude"]
    if params.pressure_levels:
        dup_cols.append("pressure_level")
    
    initial_rows = len(df)
    df = df.drop_duplicates(subset=dup_cols)
    if initial_rows - len(df) > 0:
        print(f"  {Colors.YELLOW}✓ Removed {initial_rows - len(df)} duplicate rows{Colors.RESET}")
    
    return df

def aggregate_and_save(params: ProcessingParams, df: pd.DataFrame):
    """Handle aggregation and saving of results"""
    # Temporal aggregation
    print(f"{Colors.BLUE}AGGREGATING DATA ({params.frequency.upper()}){Colors.RESET}")

    start_time = time.time()
    agg_func = aggregate_pressure_levels if params.pressure_levels else aggregate_by_frequency
    aggregated_df, unique_latlongs = agg_func(df, params.frequency)
    elapsed = time.time() - start_time
    print(f"Aggregation completed in:   {elapsed:.2f} seconds")

    # Adjust sum variables if needed
    if params.frequency in ['monthly', 'yearly']:
        adjust_sum_variables(aggregated_df, params.frequency)
    
    # Save results
    save_results(params, aggregated_df, unique_latlongs, df)
    
    return aggregated_df

def adjust_sum_variables(df: pd.DataFrame, frequency: str):
    """Adjust sum variables based on temporal frequency"""
    sum_vars_present = [col for col in df.columns if col in SUM_VARS]
    
    if not sum_vars_present:
        return
    
    try:
        if frequency == 'monthly':
            df['days_in_month'] = df['month'].apply(
                lambda m: monthrange(df['year'].iloc[0], m)[1]
            )
            for var in sum_vars_present:
                if var in df.columns:
                    df[var] = df[var] * df['days_in_month']
            df.drop('days_in_month', axis=1, inplace=True)
        elif frequency == 'yearly':
            for var in sum_vars_present:
                if var in df.columns:
                    df[var] = df[var] * 30.4375
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Error adjusting sum variables: {e}{Colors.RESET}")

def save_results(params: ProcessingParams, aggregated_df: pd.DataFrame, 
                unique_latlongs: pd.DataFrame, raw_df: pd.DataFrame):
    """Save all results to files"""

    output_dir = f"{params.request_id}_output"
    print(f"\nSaving files to output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save aggregated data
    csv_output = os.path.join(output_dir, f"{params.request_id}_{params.frequency}_data.csv")
    aggregated_df.to_csv(csv_output, index=False)
    print(f"  Saved final data to: {csv_output}")
    
    # Save unique coordinates
    csv_output = os.path.join(output_dir, f"{params.request_id}_unique_latlongs.csv")
    unique_latlongs.to_csv(csv_output, index=False)
    print(f"  Saved unique coordinates to: {csv_output}")
    
    # Save raw data
    csv_output = os.path.join(output_dir, f"{params.request_id}_raw_data.csv")
    raw_df.to_csv(csv_output, index=False)
    print(f"  Saved raw data to: {csv_output}")

def process_era5(params: ProcessingParams):
    """Main entry point for ERA5 processing"""
    ensure_cdsapi_config()
    total_start_time = time.time()

    print_processing_header(params)
    
    # Validate inputs
    validate_inputs(params)
    
    # Get bounding box if GeoJSON provided
    if params.geojson_file and not params.geojson_data:
        params.geojson_data = load_and_validate_geojson(params.geojson_file)
    
    if params.geojson_data and not (params.north and params.south and params.east and params.west):
        params.west, params.south, params.east, params.north = get_bounding_box(params.geojson_data)
    
    print_bounding_box(params)
    
    if params.geojson_data:
        print("\n\n--- GeoJSON Mini Map ---")
        draw_geojson_ascii(params.geojson_data)

    print_processing_strategy(params)
    
    # Process data (with chunking if needed)
    processed_df = process_time_chunks(params, 
        download_era5_pressure_lvl if params.pressure_levels else download_era5_single_lvl,
        lambda p, cn=1, tc=1: process_era5_data(p, (cn, tc))
    )
    final_result = aggregate_and_save(params, processed_df)
    print_processing_footer(params, final_result, total_start_time)
    return final_result

# Helper functions for printing/logging
def print_processing_header(params: ProcessingParams):
    """Print processing header information"""
    dataset_type = "PRESSURE LEVEL" if params.pressure_levels else "SINGLE LEVEL"
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}STARTING ERA5 {dataset_type} PROCESSING{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Request ID: {params.request_id}")
    print(f"Variables: {params.variables}")
    if params.pressure_levels:
        print(f"Pressure Levels: {params.pressure_levels}")
    print(f"Date Range: {params.start_date.strftime('%Y-%m-%d')} to {params.end_date.strftime('%Y-%m-%d')}")
    print(f"Frequency: {params.frequency}")
    print(f"Resolution: {params.resolution}°")
    if params.geojson_file:
        print(f"GeoJSON File: {params.geojson_file}")

def validate_inputs(params: ProcessingParams):
    """Validate all input parameters"""
    if not params.variables:
        raise ValueError("Variables list cannot be empty")
    if params.start_date > params.end_date:
        raise ValueError("Start date cannot be after end date")
    if params.pressure_levels and not params.pressure_levels:
        raise ValueError("pressure_levels must be provided for pressure level data")
    if params.geojson_file and not os.path.exists(params.geojson_file):
        raise FileNotFoundError(f"GeoJSON file not found: {params.geojson_file}")
    print(f"{Colors.GREEN}✓ All inputs validated successfully{Colors.RESET}")

def load_and_validate_geojson(geojson_file: str) -> Dict:
    """Load and validate GeoJSON file"""
    print("\n--- Loading GeoJSON File ---")
    geojson_data = load_json_with_encoding(geojson_file)
    if not is_valid_geojson(geojson_data):
        geojson_data = convert_to_geojson(geojson_data)
    print(f"{Colors.GREEN}✓ GeoJSON loaded successfully{Colors.RESET}")
    
    return geojson_data

def print_bounding_box(params: ProcessingParams):
    """Print bounding box information"""
    print("\n--- Bounding Box ---")
    print(f"{Colors.GREEN}✓ Bounding Box calculated:{Colors.RESET}")
    print(f"  North: {params.north:.4f}°")
    print(f"  South: {params.south:.4f}°")
    print(f"  East:  {params.east:.4f}°")
    print(f"  West:  {params.west:.4f}°")
    print(f"  Area:  {abs(params.east-params.west):.4f}° × {abs(params.north-params.south):.4f}°")

def print_processing_strategy(params: ProcessingParams):
    """Print processing strategy information"""
    print("\n--- Processing Strategy ---")
    use_monthly = params.frequency in ["monthly", "yearly"]
    print(f"Using monthly dataset: {use_monthly}")
    
    if use_monthly:
        total_units = (params.end_date.year - params.start_date.year) * 12 + (params.end_date.month - params.start_date.month) + 1
        max_per_chunk = 100
    else:
        total_units = (params.end_date - params.start_date).days + 1
        max_per_chunk = 14
    
    needs_chunking = total_units > max_per_chunk
    print(f"Total {'months' if use_monthly else 'days'} to process: {total_units}")
    print(f"Max {'months' if use_monthly else 'days'} per chunk: {max_per_chunk}")
    print(f"Needs chunking: {needs_chunking}")

def calculate_map_dimensions(west, east, south, north):
    """Calculate proportional width/height for ASCII map"""
    geo_width = abs(east - west)
    geo_height = abs(north - south)
    
    MIN_DIMENSION = 8
    
    if geo_width == 0 or geo_height == 0:
        return 20, 20  # Fallback for invalid bbox
    
    avg = (geo_height + geo_width) / 2
    width = int(geo_width * 20 / avg * 2)
    height = int(geo_height * 20 / avg)
    return max(width, MIN_DIMENSION), max(height, MIN_DIMENSION)

def draw_geojson_ascii(geojson_data):
    """
    Draws a mini ASCII map showing the GeoJSON polygon
    :param geojson_data: Loaded GeoJSON data
    :param width: Width of ASCII art in characters
    :param height: Height of ASCII art in characters
    """
    try:
        from shapely.geometry import shape, Polygon, MultiPolygon
        import numpy as np
        
        # Get bounding box
        west, south, east, north = get_bounding_box(geojson_data)
        
        width, height = calculate_map_dimensions(west, east, south, north)

        # Create grid
        x = np.linspace(west, east, width)
        y = np.linspace(south, north, height)
        
        # Create polygon from GeoJSON
        geom = shape(geojson_data['features'][0]['geometry'])
        
        # Draw ASCII art
        print(f"\n{Colors.BLUE}MINI MAP ({west:.2f}°W to {east:.2f}°E, {south:.2f}°S to {north:.2f}°N):{Colors.RESET}")
        print("┌" + "─" * width + "┐")
        
        for j in range(height-1, -1, -1):
            row = ["│"]
            for i in range(width):
                point = (x[i], y[j])
                if geom.contains(Point(point)):
                    row.append(f"{Colors.GREEN}■{Colors.RESET}")
                else:
                    row.append(f"{Colors.RED}·{Colors.RESET}")
            row.append("│")
            print("".join(row))
        
        print("└" + "─" * width + "┘")
        print(f" {Colors.GREEN}■{Colors.RESET} = Inside the shape")
        print(f" {Colors.RED}·{Colors.RESET} = Outside the shape")
        
    except Exception as e:
        print(f"{Colors.YELLOW}Couldn't draw mini map: {str(e)}{Colors.RESET}")

def print_processing_footer(params: ProcessingParams, result_df: pd.DataFrame, total_start_time: float):
    """Print processing footer information"""
    print(f"\n{'='*60}")
    print(f"{Colors.GREEN}PROCESSING COMPLETE{Colors.RESET}")
    print(f"{'='*60}")

    print(f"\n{Colors.CYAN}RESULTS SUMMARY:{Colors.RESET}")
    print(f"{'-'*40}")
    print(f"Variables processed: {len(params.variables)}")
    print(f"Time period:         {params.start_date} to {params.end_date}")
    print(f"Final output shape:  {result_df.shape}")

    elapsed_time = time.time() - total_start_time
    print(f"Total complete processing time: {elapsed_time:.2f} seconds")

    print("\nFirst 5 rows of aggregated data:")
    print(result_df.head())
    
    dataset_type = "PRESSURE LEVEL" if params.pressure_levels else "SINGLE LEVEL"
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}ERA5 {dataset_type} PROCESSING COMPLETED SUCCESSFULLY{Colors.RESET}")
    print(f"{'='*60}")

# Public functions
def era5ify_geojson(
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    json_file: str,
    dataset_type: str = "single",
    pressure_levels: Optional[List[str]] = None,
    frequency: str = "hourly",
    resolution: float = 0.25,
) -> pd.DataFrame:
    """Public function for processing with GeoJSON"""
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
    
    # Validate dataset type
    dataset_type = dataset_type.lower()
    if dataset_type not in ["single", "pressure"]:
        raise ValueError(f"Invalid dataset_type: {dataset_type}. Must be 'single' or 'pressure'")
    
    # Load and validate GeoJSON
    json_data = load_json_with_encoding(json_file)
    geojson_data = json_data if is_valid_geojson(json_data) else convert_to_geojson(json_data)
    temp_geojson_file = create_temp_geojson(geojson_data, request_id)
    
    try:
        params = ProcessingParams(
            request_id=request_id,
            variables=variables,
            start_date=start_dt,
            end_date=end_dt,
            frequency=frequency,
            resolution=resolution,
            pressure_levels=pressure_levels if dataset_type == "pressure" else None,
            geojson_file=temp_geojson_file,
            geojson_data=geojson_data
        )
        
        return process_era5(params)
    finally:
        cleanup_temp_files(request_id, temp_geojson_file)

def era5ify_bbox(
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    north: float,
    south: float,
    east: float,
    west: float,
    dataset_type: str = "single",
    pressure_levels: Optional[List[str]] = None,
    frequency: str = "hourly",
    resolution: float = 0.25,
) -> pd.DataFrame:
    """Public function for processing with bounding box"""
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
    
    # Validate dataset type
    dataset_type = dataset_type.lower()
    if dataset_type not in ["single", "pressure"]:
        raise ValueError(f"Invalid dataset_type: {dataset_type}. Must be 'single' or 'pressure'")
    
    # Validate bounding box
    if north <= south or east <= west:
        raise ValueError("Invalid bounding box coordinates")
    
    # Create temporary GeoJSON
    geojson_data = create_geojson_from_bbox(west, south, east, north)
    temp_geojson_file = create_temp_geojson(geojson_data, request_id)
    
    try:
        params = ProcessingParams(
            request_id=request_id,
            variables=variables,
            start_date=start_dt,
            end_date=end_dt,
            frequency=frequency,
            resolution=resolution,
            pressure_levels=pressure_levels if dataset_type == "pressure" else None,
            north=north,
            south=south,
            east=east,
            west=west
        )
        
        return process_era5(params)
    finally:
        cleanup_temp_files(request_id, temp_geojson_file)

def parse_date(date_str: str) -> dt.datetime:
    """Parse date string into datetime object"""
    try:
        parts = date_str.split('-')
        return dt.datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        raise ValueError(f"Invalid date format: {date_str}. Expected 'YYYY-M-D' or 'YYYY-MM-DD'")

def cleanup_temp_files(request_id: str, temp_geojson_file: str):
    """Clean up temporary files"""
    if os.path.exists(temp_geojson_file):
        os.remove(temp_geojson_file)
    
    temp_dir = tempfile.gettempdir()
    for pattern in [f"*{request_id}*.zip", f"*{request_id}*.nc"]:
        for file in glob.glob(os.path.join(temp_dir, pattern)):
            if os.path.exists(file):
                os.remove(file)
    
    for item in glob.glob(os.path.join(temp_dir, f"*{request_id}*")):
        if os.path.isdir(item):
            shutil.rmtree(item)