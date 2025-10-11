import datetime as dt
import glob
import logging
import math
import os
import shutil
import tempfile
import time
from calendar import monthrange
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import Point, shape
from shapely.ops import unary_union

from .config import ensure_cdsapi_config, set_v_config
from .download import (
    download_era5_pressure_lvl,
    download_era5_single_lvl,
    set_v_downloader,
)
from .processing import (
    aggregate_by_frequency,
    aggregate_pressure_levels,
    extract_download,
    filter_netcdf_by_shapefile,
    set_v_data_agg,
    set_v_data_fil,
    set_v_file_han,
    sum_vars,
)
from .util import (
    Colors,
    convert_to_geojson,
    create_geojson_from_bbox,
    create_temp_geojson,
    get_bounding_box,
    get_logger,
    is_valid_geojson,
    load_json_with_encoding,
    set_v_geoj_utl,
)

logger = get_logger(level=logging.DEBUG)
always_logger = get_logger(name="log_always", level=logging.INFO)

SUM_VARS = sum_vars


@dataclass
class ProcessingParams:
    request_id: str
    variables: List[str]
    start_date: dt.datetime
    end_date: dt.datetime
    frequency: str = "hourly"
    resolution: float = 0.25
    dataset_type: str = "single"
    pressure_levels: Optional[List[str]] = None
    north: Optional[float] = None
    south: Optional[float] = None
    east: Optional[float] = None
    west: Optional[float] = None
    geojson_file: Optional[str] = None
    geojson_data: Optional[Dict[str, Any]] = None
    dist_features: Optional[List[str]] = None


def set_verbosity(verbosity: int) -> None:

    if verbosity == 0:
        logger.setLevel(logging.WARNING)

    elif verbosity == 1:
        logger.setLevel(logging.INFO)

    elif verbosity == 2:
        logger.setLevel(logging.DEBUG)

    else:
        logger.warning(
            f"Invalid verbosity level: {verbosity}. Defaulting to WARNING level (verbosity level = 0)."
        )
        logger.setLevel(logging.WARNING)

    set_v_data_agg(verbosity)
    set_v_data_fil(verbosity)
    set_v_file_han(verbosity)
    set_v_geoj_utl(verbosity)
    set_v_config(verbosity)
    set_v_downloader(verbosity)


def download_with_retry(
    download_func: Callable[..., Optional[str]],
    params: ProcessingParams,
    chunk_id: Optional[str] = None,
) -> Optional[str]:
    """Generic download function with retry logic"""
    max_retries = 5
    retry_delay = 30

    download_args = {
        "request_id": chunk_id or params.request_id,
        "variables": params.variables,
        "start_date": params.start_date,
        "end_date": params.end_date,
        "north": params.north,
        "west": params.west,
        "south": params.south,
        "east": params.east,
        "resolution": params.resolution,
        "frequency": params.frequency,
    }

    if download_func == download_era5_pressure_lvl:
        download_args["pressure_levels"] = params.pressure_levels

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"  → Downloading ERA5 data (attempt {attempt + 1}/{max_retries + 1})..."
            )
            download_file = download_func(**download_args)
            logger.info(
                f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}"
            )
            return download_file
        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"  {Colors.RED}✗ Download attempt {attempt + 1} failed: {error_msg}{Colors.RESET}"
            )

            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error(
                    f"  {Colors.RED}✗ All {max_retries + 1} download attempts failed{Colors.RESET}"
                )
                raise e

    raise RuntimeError("Download failed after maximum retries")


def process_time_chunks(
    params: ProcessingParams,
    download_func: Callable[..., Optional[str]],
    process_func: Callable[
        [ProcessingParams, Optional[int], Optional[int]], Optional[pd.DataFrame]
    ],
) -> Optional[pd.DataFrame]:
    """Handle time-based chunking of downloads and processing"""
    use_monthly = params.frequency in ["monthly", "yearly"]

    if use_monthly:
        max_per_chunk = 100  # months
        total_units = (
            (params.end_date.year - params.start_date.year) * 12
            + (params.end_date.month - params.start_date.month)
            + 1
        )
    else:
        max_per_chunk = 14  # days
        total_units = (params.end_date - params.start_date).days + 1

    needs_chunking = total_units > max_per_chunk
    all_data: List[pd.DataFrame] = []

    if not needs_chunking:
        return process_func(params, 1, 1)

    # Chunked processing
    current_date = params.start_date
    chunk_number = 1
    total_chunks = math.ceil(total_units / max_per_chunk)

    while current_date <= params.end_date:
        chunk_params = ProcessingParams(**params.__dict__)

        # Calculate chunk dates
        if use_monthly:
            chunk_end_year = current_date.year + (
                (current_date.month - 1 + max_per_chunk - 1) // 12
            )
            chunk_end_month = ((current_date.month - 1 + max_per_chunk - 1) % 12) + 1
            next_month = dt.datetime(
                chunk_end_year, chunk_end_month, 28
            ) + dt.timedelta(days=4)
            chunk_end = min(
                next_month - dt.timedelta(days=next_month.day), params.end_date
            )
        else:
            chunk_end = min(
                current_date + dt.timedelta(days=max_per_chunk - 1), params.end_date
            )

        chunk_msg = (
            f"{Colors.CYAN}PROCESSING CHUNK {chunk_number}/{total_chunks}{Colors.RESET}\n"
            f"Date Range: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}\n"
            f"Variables:  {', '.join(params.variables)}"
        )
        if params.pressure_levels:
            chunk_msg += f"\nLevels:     {', '.join(params.pressure_levels)}"
        logger.info(chunk_msg)

        chunk_params.start_date = current_date
        chunk_params.end_date = chunk_end

        try:
            start_time = time.time()
            chunk_data = process_func(chunk_params, chunk_number, total_chunks)
            elapsed = time.time() - start_time
            logger.info(
                f"{Colors.GREEN}✓ Chunk completed in {elapsed:.1f} seconds{Colors.RESET}"
            )
            if chunk_data is not None:
                all_data.append(chunk_data)
        except Exception as e:
            logger.error(
                f"  {Colors.RED}✗ Error processing chunk {chunk_number}: {e}{Colors.RESET}"
            )

        # Prepare for next chunk
        chunk_number += 1
        current_date = chunk_end + dt.timedelta(days=1)

        if chunk_number <= total_chunks:
            time.sleep(10)  # Rate limiting

    if not all_data:
        raise ValueError("No data was successfully processed from any chunk")

    return pd.concat(all_data, ignore_index=True)


# pyright: reportUnknownMemberType=false
def process_era5_data(
    params: ProcessingParams, chunk_info: Optional[Tuple[int, int]] = None
) -> Optional[pd.DataFrame]:
    """Core processing function for both single and pressure level data"""
    chunk_number, total_chunks = chunk_info or (1, 1)

    # Determine download function
    download_func = (
        download_era5_pressure_lvl
        if params.pressure_levels
        else download_era5_single_lvl
    )

    # Download data
    chunk_id = (
        f"{params.request_id}_chunk{chunk_number}"
        if total_chunks > 1
        else params.request_id
    )
    download_file = download_with_retry(download_func, params, chunk_id)

    # Process downloaded files
    nc_files: List[str] = []
    if download_file is not None:
        nc_files = extract_download(download_file)
    datasets: List[xr.Dataset] = []

    logger.info("\nProcessing downloaded data:")
    logger.info(f"- Found {len(nc_files)} file(s)")

    for i, nc_file in enumerate(nc_files, 1):
        if not nc_file.lower().endswith(".nc"):
            continue
        logger.debug(
            f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
        )
        try:
            ds: xr.Dataset = xr.open_dataset(nc_file)
            logger.debug(f"  ✓ Loaded: Dimensions: {ds.sizes}")
            datasets.append(ds)
        except Exception as e:
            logger.error(
                f"    {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}"
            )

    if not datasets:
        raise ValueError("No valid datasets were processed")

    # Merge and convert to DataFrame
    merged_ds: xr.Dataset = xr.merge(datasets) if len(datasets) > 1 else datasets[0]

    # Apply filtering if GeoJSON provided
    if params.geojson_data:
        df = filter_netcdf_by_shapefile(
            merged_ds, params.geojson_data, params.dist_features
        )
    else:
        df = merged_ds.to_dataframe().reset_index()

    # Remove duplicates
    dup_cols = ["valid_time", "latitude", "longitude"]
    if params.pressure_levels:
        dup_cols.append("pressure_level")

    initial_rows = len(df)
    df = df.drop_duplicates(subset=dup_cols)
    if initial_rows - len(df) > 0:
        logger.debug(
            f"  {Colors.YELLOW}✓ Removed {initial_rows - len(df)} duplicate rows{Colors.RESET}"
        )

    return df


def aggregate_and_save(
    params: ProcessingParams, df: pd.DataFrame, save_raw: bool
) -> pd.DataFrame:
    """Handle aggregation and saving of results"""
    # Temporal aggregation
    logger.info(
        f"{Colors.BLUE}AGGREGATING DATA ({params.frequency.upper()}){Colors.RESET}"
    )

    start_time = time.time()
    agg_func: Callable[
        [pd.DataFrame, str, bool, Optional[List[str]]],
        Tuple[pd.DataFrame, pd.DataFrame],
    ] = (
        aggregate_pressure_levels if params.pressure_levels else aggregate_by_frequency
    )
    aggregated_df, unique_latlongs = agg_func(
        df, params.frequency, False, params.dist_features
    )
    elapsed = time.time() - start_time
    logger.info(f"Aggregation completed in:   {elapsed:.2f} seconds")

    # Adjust sum variables if needed
    if params.frequency in ["monthly", "yearly"]:
        adjust_sum_variables(aggregated_df, params.frequency)

    # Save results
    save_results(params, aggregated_df, unique_latlongs, df, save_raw)

    return aggregated_df


def adjust_sum_variables(df: pd.DataFrame, frequency: str) -> None:
    """Adjust sum variables based on temporal frequency"""
    sum_vars_present = [col for col in df.columns if col in SUM_VARS]

    if not sum_vars_present:
        return

    try:
        if frequency == "monthly":

            def _days_in_month(row: pd.Series) -> int:
                return monthrange(int(row["year"]), int(row["month"]))[1]

            df["days_in_month"] = df.apply(_days_in_month, axis=1)
            for var in sum_vars_present:
                if var in df.columns:
                    df[var] = df[var] * df["days_in_month"]
            df.drop("days_in_month", axis=1, inplace=True)
        elif frequency == "yearly":
            for var in sum_vars_present:
                if var in df.columns:
                    df[var] = df[var] * 30.4375
    except Exception as e:
        error_msg = f"Error adjusting sum variables: {str(e)}"
        logger.warning(error_msg)


def save_results(
    params: ProcessingParams,
    aggregated_df: pd.DataFrame,
    unique_latlongs: pd.DataFrame,
    raw_df: pd.DataFrame,
    save_raw: bool,
) -> None:
    """Save all results to files"""

    output_dir = f"{params.request_id}_output"
    always_logger.info(f"\nSaving files to output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    # Save aggregated data
    csv_output = os.path.join(
        output_dir, f"{params.request_id}_{params.frequency}_data.csv"
    )
    aggregated_df.to_csv(csv_output, index=False)
    always_logger.info(f"  Saved final data to: {csv_output}")

    # Save unique coordinates
    csv_output = os.path.join(output_dir, f"{params.request_id}_unique_latlongs.csv")
    unique_latlongs.to_csv(csv_output, index=False)
    always_logger.info(f"  Saved unique coordinates to: {csv_output}")

    if save_raw:
        # Drop unwanted columns
        raw_df = raw_df.drop(columns=["number", "expver"], errors="ignore")
        # Save raw data
        csv_output = os.path.join(output_dir, f"{params.request_id}_raw_data.csv")
        raw_df.to_csv(csv_output, index=False)
        always_logger.info(f"  Saved raw data to: {csv_output}")


def process_era5(params: ProcessingParams, save_raw: bool) -> pd.DataFrame:
    """Main entry point for ERA5 processing"""
    ensure_cdsapi_config()
    total_start_time = time.time()

    print_processing_header(params)

    # Validate inputs
    validate_inputs(params)

    # Get bounding box if GeoJSON provided
    if params.geojson_file and not params.geojson_data:
        params.geojson_data = load_and_validate_geojson(params.geojson_file)

    if params.geojson_data and not (
        params.north and params.south and params.east and params.west
    ):
        params.west, params.south, params.east, params.north = get_bounding_box(
            params.geojson_data
        )

    print_bounding_box(params)

    if params.geojson_data:
        print("\n\n--- GeoJSON Mini Map ---")
        draw_geojson_ascii(params.geojson_data)

    print_processing_strategy(params)

    # Process data (with chunking if needed)
    processed_df = process_time_chunks(
        params,
        (
            download_era5_pressure_lvl
            if params.pressure_levels
            else download_era5_single_lvl
        ),
        lambda p, cn, tc: process_era5_data(
            p, (cn, tc) if cn is not None and tc is not None else None
        ),
    )

    if processed_df is None:
        raise ValueError("No valid data processed during chunking.")

    final_result = aggregate_and_save(params, processed_df, save_raw)
    print_processing_footer(params, final_result, total_start_time)
    return final_result


# Helper functions for printing/logging
def print_processing_header(params: ProcessingParams) -> None:
    """Print processing header information"""
    dataset_type = "PRESSURE LEVEL" if params.pressure_levels else "SINGLE LEVEL"
    always_logger.info(f"\n{'='*60}")
    always_logger.info(
        f"{Colors.BLUE}STARTING ERA5 {dataset_type} PROCESSING{Colors.RESET}"
    )
    always_logger.info(f"{'='*60}")
    always_logger.info(f"Request ID: {params.request_id}")
    always_logger.info(f"Variables: {params.variables}")
    if params.pressure_levels:
        always_logger.info(f"Pressure Levels: {params.pressure_levels}")
    always_logger.info(
        f"Date Range: {params.start_date.strftime('%Y-%m-%d')} to {params.end_date.strftime('%Y-%m-%d')}"
    )
    always_logger.info(f"Frequency: {params.frequency}")
    always_logger.info(f"Resolution: {params.resolution}°")
    if params.geojson_file:
        always_logger.info(f"GeoJSON File: {params.geojson_file}")


def validate_inputs(params: ProcessingParams) -> None:
    """Validate all input parameters"""
    if not params.variables:
        raise ValueError("Variables list cannot be empty")
    if params.start_date > params.end_date:
        raise ValueError("Start date cannot be after end date")
    if params.dataset_type == "pressure" and not params.pressure_levels:
        raise ValueError("pressure_levels must be provided for pressure level data")
    if params.geojson_file and not os.path.exists(params.geojson_file):
        raise FileNotFoundError(f"GeoJSON file not found: {params.geojson_file}")
    logger.info(f"{Colors.GREEN}✓ All inputs validated successfully{Colors.RESET}")


def load_and_validate_geojson(geojson_file: str) -> Dict[str, Any]:
    """Load and validate GeoJSON file"""
    logger.debug("\n--- Loading GeoJSON File ---")
    geojson_data = load_json_with_encoding(geojson_file)
    if not is_valid_geojson(geojson_data):
        geojson_data = convert_to_geojson(geojson_data)
    logger.debug(f"{Colors.GREEN}✓ GeoJSON loaded successfully{Colors.RESET}")

    return geojson_data


def print_bounding_box(params: ProcessingParams) -> None:
    """Print bounding box information"""
    logger.info("\n--- Bounding Box ---")
    logger.info(f"{Colors.GREEN}✓ Bounding Box calculated:{Colors.RESET}")
    logger.info(f"  North: {params.north:.4f}°")
    logger.info(f"  South: {params.south:.4f}°")
    logger.info(f"  East:  {params.east:.4f}°")
    logger.info(f"  West:  {params.west:.4f}°")
    if params.north and params.south and params.east and params.west:
        logger.info(
            f"  Area:  {abs(params.east-params.west):.4f}° × {abs(params.north-params.south):.4f}°"
        )


def print_processing_strategy(params: ProcessingParams) -> None:
    """Print processing strategy information"""
    logger.debug("\n--- Processing Strategy ---")
    use_monthly = params.frequency in ["monthly", "yearly"]
    logger.debug(f"Using monthly dataset: {use_monthly}")

    if use_monthly:
        total_units = (
            (params.end_date.year - params.start_date.year) * 12
            + (params.end_date.month - params.start_date.month)
            + 1
        )
        max_per_chunk = 100
    else:
        total_units = (params.end_date - params.start_date).days + 1
        max_per_chunk = 14

    needs_chunking = total_units > max_per_chunk
    logger.debug(
        f"Total {'months' if use_monthly else 'days'} to process: {total_units}"
    )
    logger.debug(
        f"Max {'months' if use_monthly else 'days'} per chunk: {max_per_chunk}"
    )
    logger.debug(f"Needs chunking: {needs_chunking}")


def calculate_map_dimensions(
    west: float, east: float, south: float, north: float
) -> Tuple[int, int]:
    """Calculate proportional width/height for ASCII map"""
    geo_width = abs(east - west)
    geo_height = abs(north - south)

    MIN_DIMENSION = 8

    if geo_width == 0 or geo_height == 0:
        return 15, 15  # Fallback for invalid bbox

    avg = (geo_height + geo_width) / 2
    width = int(geo_width * 15 / avg * 2)
    height = int(geo_height * 15 / avg)
    return max(width, MIN_DIMENSION), max(height, MIN_DIMENSION)


def draw_geojson_ascii(geojson_data: Dict[str, Any]) -> None:
    """
    Draws a mini ASCII map showing the GeoJSON polygons.
    :param geojson_data: Loaded GeoJSON data (must be FeatureCollection)
    """
    try:
        # Combine all geometries in the GeoJSON into a single geometry
        geometries = [
            shape(feature["geometry"]) for feature in geojson_data.get("features", [])
        ]
        if len(geometries) > 100:
            print("Too many features in GeoJSON (more than 100). Skipping mini map.")
            return
        if not geometries:
            print("No geometries found in GeoJSON.")
            return

        combined_geom = unary_union(geometries)
        combined_geom = combined_geom.simplify(0.05, preserve_topology=True)

        # Get bounding box
        west, south, east, north = get_bounding_box(geojson_data)

        # Calculate dimensions of the ASCII grid
        width, height = calculate_map_dimensions(west, east, south, north)

        # Generate grid coordinates
        x = np.linspace(west, east, width)
        y = np.linspace(south, north, height)

        # Print header
        print(
            f"\n{Colors.BLUE}MINI MAP (Longitude: {west:.2f}° to {east:.2f}°, Latitude: {south:.2f}° to {north:.2f}°):{Colors.RESET}"
        )
        print("┌" + "─" * width + "┐")

        # Render the ASCII map
        for j in range(height - 1, -1, -1):
            row = ["│"]
            for i in range(width):
                point = Point(x[i], y[j])
                if combined_geom.covers(point):
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


def print_processing_footer(
    params: ProcessingParams, result_df: pd.DataFrame, total_start_time: float
) -> None:
    """Print processing footer information"""
    always_logger.info(f"\n{'='*60}")
    always_logger.info(f"{Colors.GREEN}PROCESSING COMPLETE{Colors.RESET}")
    always_logger.info(f"{'='*60}")

    always_logger.info(f"\n{Colors.CYAN}RESULTS SUMMARY:{Colors.RESET}")
    always_logger.info(f"{'-'*40}")
    always_logger.info(f"Variables processed: {len(params.variables)}")
    always_logger.info(
        f"Time period:         {params.start_date.date()} to {params.end_date.date()}"
    )
    always_logger.info(f"Final output shape:  {result_df.shape}")

    elapsed_time = time.time() - total_start_time
    always_logger.info(f"Total complete processing time: {elapsed_time:.2f} seconds")

    always_logger.info("\nFirst 5 rows of aggregated data:")
    always_logger.info(result_df.head())

    dataset_type = "PRESSURE LEVEL" if params.pressure_levels else "SINGLE LEVEL"
    always_logger.info(f"\n{'='*60}")
    always_logger.info(
        f"{Colors.BLUE}ERA5 {dataset_type} PROCESSING COMPLETED SUCCESSFULLY{Colors.RESET}"
    )
    always_logger.info(f"{'='*60}")


# Public functions
def era5ify_geojson(
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    json_file: str,
    dist_features: Optional[List[str]] = None,
    dataset_type: str = "single",
    pressure_levels: Optional[List[str]] = None,
    frequency: str = "hourly",
    resolution: float = 0.25,
    verbosity: int = 0,
    save_raw: bool = True,
) -> pd.DataFrame:
    """
    Public function for querying data for a GeoJSON.

    Args:
        request_id (str): Unique identifier for the request.
        variables (List[str]): List of variables to download.
        start_date (str): Start date of the data in 'YYYY-M-D' or 'YYYY-MM-DD' format.
        end_date (str): End date of the data in 'YYYY-M-D' or 'YYYY-MM-DD' format.
        json_file (str): Path to the GeoJSON file.
        dist_features (List[str] | None, optional): List of feature properties to distinguish different areas in the GeoJSON. Defaults to None.
        dataset_type (str, optional): Type of dataset. Either 'single' (single level) or 'pressure' (pressure level). Defaults to 'single'.
        pressure_levels (List[str] | None, optional): List of pressure levels to download (e.g., ["1000", "925", "850"]). Defaults to None.
        frequency (str, optional): Frequency of the data ('hourly', 'daily', 'weekly', 'monthly', 'yearly'). Defaults to 'hourly'.
        resolution (float, optional): Spatial resolution in degrees (0.25, 0.1, 0.5, etc.). Defaults to 0.25, minimum is 0.1.
        verbosity (int, optional): Verbosity level (0 for no output, 1 for info output, 2 for debug/complete output). Defaults to 0.
        save_raw (bool, optional): Whether to save the raw data. Defaults to True.

    Returns:
        DataFrame: A DataFrame containing the processed data for the region described by GeoJSON.
    """
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    set_verbosity(verbosity)

    # Validate dataset type
    dataset_type = dataset_type.lower()
    if dataset_type not in ["single", "pressure"]:
        raise ValueError(
            f"Invalid dataset_type: {dataset_type}. Must be 'single' or 'pressure'"
        )

    # Load and validate GeoJSON
    json_data = load_json_with_encoding(json_file)
    geojson_data = (
        json_data if is_valid_geojson(json_data) else convert_to_geojson(json_data)
    )
    temp_geojson_file = create_temp_geojson(geojson_data, request_id)

    try:
        params = ProcessingParams(
            request_id=request_id,
            variables=variables,
            start_date=start_dt,
            end_date=end_dt,
            frequency=frequency,
            resolution=resolution,
            dataset_type=dataset_type,
            pressure_levels=pressure_levels if dataset_type == "pressure" else None,
            geojson_file=temp_geojson_file,
            geojson_data=geojson_data,
            dist_features=dist_features,
        )
        return process_era5(params, save_raw)

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
    verbosity: int = 0,
    save_raw: bool = True,
) -> pd.DataFrame:
    """
    Public function for querying data for a defined bounding box (north, south, east, west bounds).

    Args:
        request_id (str): Unique identifier for the request.
        variables (List[str]): List of variables to download.
        start_date (str): Start date of the data in 'YYYY-M-D' or 'YYYY-MM-DD' format.
        end_date (str): End date of the data in 'YYYY-M-D' or 'YYYY-MM-DD' format.
        north (float): Northern bound of the bounding box.
        south (float): Southern bound of the bounding box.
        east (float): Eastern bound of the bounding box.
        west (float): Western bound of the bounding box.
        dataset_type (str, optional): Type of dataset. Either 'single' (single level) or 'pressure' (pressure level). Defaults to 'single'.
        pressure_levels (List[str] | None, optional): List of pressure levels to download (e.g., ["1000", "925", "850"]). Defaults to None.
        frequency (str, optional): Frequency of the data ('hourly', 'daily', 'weekly', 'monthly', 'yearly'). Defaults to 'hourly'.
        resolution (float, optional): Spatial resolution in degrees (0.25, 0.1, 0.5, etc.). Defaults to 0.25, minimum is 0.1.
        verbosity (int, optional): Verbosity level (0 for no output, 1 for info output, 2 for debug/complete output). Defaults to 0.
        save_raw (bool, optional): Whether to save the raw data. Defaults to True.

    Returns:
        DataFrame: A DataFrame containing the processed data for the specified bbox.
    """
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    set_verbosity(verbosity)

    # Validate dataset type
    dataset_type = dataset_type.lower()
    if dataset_type not in ["single", "pressure"]:
        raise ValueError(
            f"Invalid dataset_type: {dataset_type}. Must be 'single' or 'pressure'"
        )

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
            dataset_type=dataset_type,
            pressure_levels=pressure_levels if dataset_type == "pressure" else None,
            north=north,
            south=south,
            east=east,
            west=west,
            dist_features=None,
        )
        return process_era5(params, save_raw)

    finally:
        cleanup_temp_files(request_id, temp_geojson_file)


def era5ify_point(
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    latitude: float,
    longitude: float,
    dataset_type: str = "single",
    pressure_levels: Optional[List[str]] = None,
    frequency: str = "hourly",
    verbosity: int = 0,
    save_raw: bool = True,
) -> pd.DataFrame:
    """
    Public function for querying data for a single geographical point (latitude, longitude).

    Args:
        request_id (str): Unique identifier for the request.
        variables (List[str]): List of variables to download.
        start_date (str): Start date of the data in 'YYYY-M-D' or 'YYYY-MM-DD' format.
        end_date (str): End date of the data in 'YYYY-M-D' or 'YYYY-MM-DD' format.
        latitude (float): Latitude of the point of interest.
        longitude (float): Longitude of the point of interest.
        dataset_type (str, optional): Type of dataset. Either 'single' (single level) or 'pressure' (pressure level). Defaults to 'single'.
        pressure_levels (List[str] | None, optional): List of pressure levels to download (e.g., ["1000", "925", "850"]). Defaults to None.
        frequency (str, optional): Frequency of the data ('hourly', 'daily', 'weekly', 'monthly', 'yearly'). Defaults to 'hourly'.
        verbosity (int, optional): Verbosity level (0 for no output, 1 for info output, 2 for debug/complete output). Defaults to 0.
        save_raw (bool, optional): Whether to save the raw data. Defaults to True.

    Returns:
        DataFrame: A DataFrame containing the processed data for the specified point.
    """

    # Validate coordinates
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise ValueError(
            f"Invalid longitude: {longitude}. Must be between -180 and 180"
        )

    set_verbosity(verbosity)

    # Create a small circular GeoJSON around the point
    # Using 0.06 degree radius (0.12 degree diameter) to capture nearest ERA5 grid point
    radius_degrees = 0.06

    # Generate circle points (simple approximation)
    num_points = 16  # Number of points to approximate the circle
    circle_coords: List[List[float]] = []

    # Handle antimeridian crossing by shifting longitude away from ±180°
    working_longitude = longitude
    if abs(longitude) > 179.9:  # Very close to antimeridian
        # Shift slightly away from the antimeridian for circle calculation
        if longitude > 0:
            working_longitude = 179.9  # Use 179.9° instead of 180°
        else:
            working_longitude = -179.9  # Use -179.9° instead of -180°

    # Handle polar regions (within 1 degree of poles)
    if abs(latitude) > 89.0:
        # Near poles: create a small square instead of circle to avoid singularity
        # This ensures we capture nearby grid points without mathematical issues
        lat_offset = radius_degrees
        lon_offset = radius_degrees * 2  # Wider longitude range near poles

        # Create a square around the pole
        square_coords = [
            [longitude - lon_offset, latitude - lat_offset],
            [longitude + lon_offset, latitude - lat_offset],
            [longitude + lon_offset, min(latitude + lat_offset, 90.0)],
            [longitude - lon_offset, min(latitude + lat_offset, 90.0)],
            [longitude - lon_offset, latitude - lat_offset],  # Close the polygon
        ]

        # Ensure longitudes are within valid range
        circle_coords = []
        for lon, lat in square_coords:
            # Normalize longitude to [-180, 180]
            while lon > 180:
                lon -= 360
            while lon < -180:
                lon += 360
            # Clamp latitude to valid range
            lat = max(-90, min(90, lat))
            circle_coords.append([lon, lat])
    else:
        # Normal case: create circular polygon
        for i in range(num_points + 1):  # +1 to close the polygon
            angle = 2 * math.pi * i / num_points
            lat_offset = radius_degrees * math.cos(angle)
            lon_offset = (
                radius_degrees * math.sin(angle) / math.cos(math.radians(latitude))
            )

            circle_lat = max(-90, min(90, latitude + lat_offset))
            circle_lon = working_longitude + lon_offset

            # Normalize longitude to [-180, 180]
            while circle_lon > 180:
                circle_lon -= 360
            while circle_lon < -180:
                circle_lon += 360

            circle_coords.append([circle_lon, circle_lat])

    # Create GeoJSON structure
    geojson_data: Dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": f"point_{request_id}",
                    "center_lat": latitude,
                    "center_lon": longitude,
                },
                "geometry": {"type": "Polygon", "coordinates": [circle_coords]},
            }
        ],
    }

    # Create temporary GeoJSON file
    temp_geojson_file = create_temp_geojson(geojson_data, f"{request_id}_point")

    try:
        # Call the existing geojson function with high resolution to get nearest point
        return era5ify_geojson(
            request_id=f"{request_id}",
            variables=variables,
            start_date=start_date,
            end_date=end_date,
            json_file=temp_geojson_file,
            dataset_type=dataset_type,
            pressure_levels=pressure_levels,
            frequency=frequency,
            resolution=0.1,
            verbosity=verbosity,
            save_raw=save_raw,
        )
    finally:
        pass


def parse_date(date_str: str) -> dt.datetime:
    """Parse date string into datetime object"""
    try:
        parts = date_str.split("-")
        return dt.datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        raise ValueError(
            f"Invalid date format: {date_str}. Expected 'YYYY-M-D' or 'YYYY-MM-DD'"
        )


def cleanup_temp_files(request_id: str, temp_geojson_file: str) -> None:
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
