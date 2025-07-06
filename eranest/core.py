import os
import sys
import json
import xarray as xr
import pandas as pd
from typing import List, Optional
import datetime as dt
import math
import glob, tempfile, shutil
import time
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

def download_with_retry(chunk_id, variables, start_dt, end_dt, north, west, south, east, resolution, frequency):
    """Helper function to download ERA5 data with retry logic"""
    max_retries = 5
    retry_delay = 30
    for attempt in range(max_retries + 1):
        try:
            print(f"  → Downloading ERA5 data (attempt {attempt + 1}/{max_retries + 1})...")
            download_file = download_era5_single_lvl(
                chunk_id,
                variables,
                start_dt,
                end_dt,
                north,
                west,
                south,
                east,
                resolution,
                frequency,
            )
            print(f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")
            return download_file
        except Exception as e:
            error_msg = str(e)
            print(f"  {Colors.RED}✗ Download attempt {attempt + 1} failed: {error_msg}{Colors.RESET}")
                
            # Check if it's a connection-related error
            is_connection_error = any(keyword in error_msg.lower() for keyword in [
                'httpsconnectionpool', 'max retries exceeded', 'connection', 
                'timeout', 'network', 'ssl', 'certificate'
            ])
                
            if attempt < max_retries:
                if is_connection_error:
                    print(f"  {Colors.YELLOW}→ Connection error detected. Retrying in {retry_delay} seconds...{Colors.RESET}")
                else:
                    print(f"  {Colors.YELLOW}→ Error encountered. Retrying in {retry_delay} seconds...{Colors.RESET}")
                time.sleep(retry_delay)
            else:
                print(f"  {Colors.RED}✗ All {max_retries + 1} download attempts failed{Colors.RESET}")
                raise e

def process_era5_single_lvl(
    request_id: str,
    variables: List[str],
    start_date: dt.datetime,
    end_date: dt.datetime,
    geojson_file: str,
    frequency: str = "hourly",
    resolution: float = 0.25,
) -> pd.DataFrame:
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
    ensure_cdsapi_config()
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}STARTING ERA5 DATA PROCESSING{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    print(f"Variables: {variables}")
    print(
        f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
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
    print(f"{Colors.GREEN}✓ All inputs validated successfully{Colors.RESET}")

    # Load GeoJSON file with encoding handling
    print("\n--- Loading GeoJSON File ---")
    try:
        # Try different encodings
        encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]
        geojson_data = None

        print(f"Attempting to load: {geojson_file}")
        for i, encoding in enumerate(encodings, 1):
            try:
                print(f"  Trying encoding {i}/{len(encodings)}: {encoding}")
                with open(geojson_file, "r", encoding=encoding) as f:
                    geojson_data = json.load(f)
                print(f"{Colors.GREEN}✓ Successfully loaded GeoJSON file with {encoding} encoding{Colors.RESET}")
                break
            except UnicodeDecodeError as e:
                print(f"  ✗ Failed with {encoding}: {str(e)[:50]}...")
                continue
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON decode error with {encoding}: {str(e)[:50]}...")
                continue

        if geojson_data is None:
            raise ValueError(
                f"Could not load {geojson_file} as valid JSON with any common encoding"
            )

        # Validate GeoJSON structure
        if "features" not in geojson_data:
            print(
                f"{Colors.YELLOW}Warning: GeoJSON doesn't have 'features' key, attempting to process anyway{Colors.RESET}"
            )
        else:
            print(f"{Colors.GREEN}✓ GeoJSON contains {len(geojson_data['features'])} feature(s){Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error loading GeoJSON file: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Get bounding box coordinates
    print("\n--- Calculating Bounding Box ---")
    try:
        west, south, east, north = get_bounding_box(geojson_data)
        print(f"{Colors.GREEN}✓ Bounding Box calculated:{Colors.RESET}")
        print(f"  North: {north:.4f}°")
        print(f"  South: {south:.4f}°")
        print(f"  East:  {east:.4f}°")
        print(f"  West:  {west:.4f}°")
        print(f"  Area:  {abs(east-west):.4f}° × {abs(north-south):.4f}°")
    except Exception as e:
        print(f"{Colors.RED}✗ Error calculating bounding box: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Determine processing strategy
    print("\n--- Determining Processing Strategy ---")
    use_monthly = frequency in ["monthly", "yearly"]
    print(f"Using monthly dataset: {use_monthly}")

    if use_monthly:
        max_months_per_chunk = 100
        total_months = (
            (end_date.year - start_date.year) * 12
            + (end_date.month - start_date.month)
            + 1
        )
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
            print(f"{Colors.CYAN}CHUNK {chunk_number}/{total_chunks}{Colors.RESET}")
            print(f"{'='*50}")

            # Calculate chunk end date (last day of the chunk)
            chunk_end_year = current_date.year + (
                (current_date.month - 1 + max_months_per_chunk - 1) // 12
            )
            chunk_end_month = (
                (current_date.month - 1 + max_months_per_chunk - 1) % 12
            ) + 1
            # Last day of chunk_end_month
            next_month = dt.datetime(
                chunk_end_year, chunk_end_month, 28
            ) + dt.timedelta(days=4)
            last_day = next_month - dt.timedelta(days=next_month.day)
            chunk_end = min(last_day, end_date)

            print(
                f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}"
            )

            try:
                download_file = download_with_retry(
                    f"{request_id}_chunk{chunk_number}",
                    variables,
                    current_date,
                    chunk_end,
                    north,
                    west,
                    south,
                    east,
                    resolution,
                    frequency,
                )

                print("  → Extracting files...")
                nc_files = extract_download(download_file)
                print(f"  {Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

                chunk_datasets = []
                print("  → Processing NetCDF files...")
                for i, nc_file in enumerate(nc_files, 1):
                    if not nc_file.lower().endswith(".nc"):
                        print(f"    Skipping non-NetCDF file: {nc_file}")
                        continue
                    try:
                        print(
                            f"    Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                        )
                        ds = xr.open_dataset(nc_file)
                        chunk_datasets.append(ds)
                        print(f"    ✓ Loaded dataset with shape: {dict(ds.dims)}")
                    except Exception as e:
                        print(f"    {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

                if not chunk_datasets:
                    print(f"  {Colors.RED}✗ No datasets were successfully processed for this chunk{Colors.RESET}")
                    chunk_number += 1
                    next_month = chunk_end + dt.timedelta(days=1)
                    current_date = next_month
                    continue

                print("  → Merging datasets...")
                merged_chunk_ds = (
                    xr.merge(chunk_datasets)
                    if len(chunk_datasets) > 1
                    else chunk_datasets[0]
                )
                print(f"  {Colors.GREEN}✓ Merged dataset shape: {dict(merged_chunk_ds.dims)}{Colors.RESET}")

                print("  → Filtering by shapefile...")
                filtered_chunk_df = filter_netcdf_by_shapefile(
                    merged_chunk_ds, geojson_data
                )
                print(f"  {Colors.GREEN}✓ Filtered data shape: {filtered_chunk_df.shape}{Colors.RESET}")

                all_filtered_data.append(filtered_chunk_df)

                chunk_time = time.time() - chunk_start_time
                print(f"  {Colors.GREEN}✓ Chunk completed in {chunk_time:.2f} seconds{Colors.RESET}")

            except Exception as e:
                print(
                    f"  {Colors.RED}✗ Error processing chunk {chunk_number} after all retries: {e}{Colors.RESET}", file=sys.stderr
                )
                # Continue with next chunk instead of failing completely

            chunk_number += 1
            next_month = chunk_end + dt.timedelta(days=1)
            current_date = next_month

            if chunk_number <= total_chunks:
                print("  → Waiting 10 seconds before next chunk...")
                time.sleep(10)

        if not all_filtered_data:
            print(
                f"{Colors.RED}✗ No data was successfully processed from any chunk{Colors.RESET}", file=sys.stderr
            )
            sys.exit(1)

        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"{Colors.GREEN}✓ Combined data shape: {filtered_df.shape}{Colors.RESET}")

        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(
            subset=["valid_time", "latitude", "longitude"]
        )
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
            print(f"{Colors.CYAN}CHUNK {chunk_number}/{total_chunks}{Colors.RESET}")
            print(f"{'='*50}")

            chunk_end = min(
                current_date + dt.timedelta(days=max_days_per_chunk - 1), end_date
            )
            print(
                f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}"
            )

            try:
                download_file = download_with_retry(
                    f"{request_id}_chunk{chunk_number}",
                    variables,
                    current_date,
                    chunk_end,
                    north,
                    west,
                    south,
                    east,
                    resolution,
                    frequency,
                )

                print("  → Extracting files...")
                nc_files = extract_download(download_file)
                print(f"  {Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

                chunk_datasets = []
                print("  → Processing NetCDF files...")
                for i, nc_file in enumerate(nc_files, 1):
                    if not nc_file.lower().endswith(".nc"):
                        print(f"    Skipping non-NetCDF file: {nc_file}")
                        continue
                    try:
                        print(
                            f"    Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                        )
                        ds = xr.open_dataset(nc_file)
                        chunk_datasets.append(ds)
                        print(f"    ✓ Loaded dataset with shape: {dict(ds.dims)}")
                    except Exception as e:
                        print(f"    {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

                if not chunk_datasets:
                    print(f"  {Colors.RED}✗ No datasets were successfully processed for this chunk{Colors.RESET}")
                    chunk_number += 1
                    current_date = chunk_end + dt.timedelta(days=1)
                    continue

                print("  → Merging datasets...")
                merged_chunk_ds = (
                    xr.merge(chunk_datasets)
                    if len(chunk_datasets) > 1
                    else chunk_datasets[0]
                )
                print(f"  {Colors.GREEN}✓ Merged dataset shape: {dict(merged_chunk_ds.dims)}{Colors.RESET}")

                print("  → Filtering by shapefile...")
                filtered_chunk_df = filter_netcdf_by_shapefile(
                    merged_chunk_ds, geojson_data
                )
                print(f"  {Colors.GREEN}✓ Filtered data shape: {filtered_chunk_df.shape}{Colors.RESET}")

                all_filtered_data.append(filtered_chunk_df)

                chunk_time = time.time() - chunk_start_time
                print(f"  {Colors.GREEN}✓ Chunk completed in {chunk_time:.2f} seconds{Colors.RESET}")

            except Exception as e:
                print(
                    f"  {Colors.RED}✗ Error processing chunk {chunk_number} after all retries: {e}{Colors.RESET}", file=sys.stderr
                )
                # Continue with next chunk instead of failing completely

            chunk_number += 1
            current_date = chunk_end + dt.timedelta(days=1)

            if chunk_number <= total_chunks:
                print("  → Waiting 10 seconds before next chunk...")
                time.sleep(10)

        if not all_filtered_data:
            print(
                f"{Colors.RED}✗ No data was successfully processed from any chunk{Colors.RESET}", file=sys.stderr
            )
            sys.exit(1)

        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"{Colors.GREEN}✓ Combined data shape: {filtered_df.shape}{Colors.RESET}")

        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(
            subset=["valid_time", "latitude", "longitude"]
        )
        removed_duplicates = initial_rows - len(filtered_df)

    elif not needs_chunking and use_monthly:
        # --- Case 3: Does NOT need chunking, needs monthly dataset ---
        print(f"Processing as a single chunk ({total_months} months)... C3")

        try:
            download_file = download_with_retry(
                request_id,
                variables,
                start_date,
                end_date,
                north,
                west,
                south,
                east,
                resolution,
                frequency,
            )

            print("→ Extracting files...")
            nc_files = extract_download(download_file)
            print(f"{Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

            all_datasets = []
            print("→ Processing NetCDF files...")
            for i, nc_file in enumerate(nc_files, 1):
                if not nc_file.lower().endswith(".nc"):
                    print(f"  Skipping non-NetCDF file: {nc_file}")
                    continue
                try:
                    print(
                        f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                    )
                    ds = xr.open_dataset(nc_file)
                    all_datasets.append(ds)
                    print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")
                except Exception as e:
                    print(f"  {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

            if not all_datasets:
                print(f"{Colors.RED}✗ No datasets were successfully processed{Colors.RESET}", file=sys.stderr)
                sys.exit(1)

            print("→ Merging datasets...")
            merged_ds = (
                xr.merge(all_datasets) if len(all_datasets) > 1 else all_datasets[0]
            )
            print(f"{Colors.GREEN}✓ Merged dataset shape: {dict(merged_ds.dims)}{Colors.RESET}")

            print("→ Filtering by shapefile...")
            filtered_df = filter_netcdf_by_shapefile(merged_ds, geojson_data)
            print(f"{Colors.GREEN}✓ Filtered data shape: {filtered_df.shape}{Colors.RESET}")

            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(
                subset=["valid_time", "latitude", "longitude"]
            )
            removed_duplicates = initial_rows - len(filtered_df)

        except Exception as e:
            print(f"{Colors.RED}✗ Error in single monthly processing after all retries: {e}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

    else:
        # --- Case 4: Does NOT need chunking, does NOT need monthly dataset ---
        print(f"Processing as a single chunk ({total_days} days)... C4")

        try:
            download_file = download_with_retry(
                request_id,
                variables,
                start_date,
                end_date,
                north,
                west,
                south,
                east,
                resolution,
                frequency,
            )

            print("→ Extracting files...")
            nc_files = extract_download(download_file)
            print(f"{Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

            all_datasets = []
            print("→ Processing NetCDF files...")
            for i, nc_file in enumerate(nc_files, 1):
                if not nc_file.lower().endswith(".nc"):
                    print(f"  Skipping non-NetCDF file: {nc_file}")
                    continue
                try:
                    print(
                        f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                    )
                    ds = xr.open_dataset(nc_file)
                    all_datasets.append(ds)
                    print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")
                except Exception as e:
                    print(f"  {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

            if not all_datasets:
                print(f"{Colors.RED}✗ No datasets were successfully processed{Colors.RESET}", file=sys.stderr)
                sys.exit(1)

            print("→ Merging datasets...")
            merged_ds = (
                xr.merge(all_datasets) if len(all_datasets) > 1 else all_datasets[0]
            )
            print(f"{Colors.GREEN}✓ Merged dataset shape: {dict(merged_ds.dims)}{Colors.RESET}")

            print("→ Filtering by shapefile...")
            filtered_df = filter_netcdf_by_shapefile(merged_ds, geojson_data)
            print(f"{Colors.GREEN}✓ Filtered data shape: {filtered_df.shape}{Colors.RESET}")

            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(
                subset=["valid_time", "latitude", "longitude"]
            )
            removed_duplicates = initial_rows - len(filtered_df)

        except Exception as e:
            print(f"{Colors.RED}✗ Error in single daily processing after all retries: {e}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

    # Aggregate by frequency (same for all cases)
    print(f"\n--- Temporal Aggregation ({frequency}) ---")
    try:
        print("→ Performing temporal aggregation...")
        aggregation_start_time = time.time()
        (aggregated_df, unique_latlongs) = aggregate_by_frequency(
            filtered_df, frequency
        )
        aggregation_time = time.time() - aggregation_start_time
        print(f"{Colors.GREEN}✓ Aggregation completed in {aggregation_time:.2f} seconds{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Aggregated data shape: {aggregated_df.shape}{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Unique lat/long combinations: {len(unique_latlongs)}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}✗ Error during aggregation: {e}{Colors.RESET}", file=sys.stderr)
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
        print(f"{Colors.GREEN}✓ Aggregated data exported to: {csv_output}{Colors.RESET}")

        # Save unique lat/longs to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_unique_latlongs.csv")
        unique_latlongs.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Unique lat/longs exported to: {csv_output}{Colors.RESET}")

        # Save raw data to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_raw_data.csv")
        filtered_df.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Raw data exported to: {csv_output}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error saving results: {e}{Colors.RESET}", file=sys.stderr)
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
        print(f"{Colors.BLUE}ERA5 DATA PROCESSING COMPLETED SUCCESSFULLY{Colors.RESET}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Error generating summary statistics: {e}{Colors.RESET}", file=sys.stderr)

    return aggregated_df

def process_era5_single_lvl_no_filter(
    request_id: str,
    variables: List[str],
    start_date: dt.datetime,
    end_date: dt.datetime,
    north: float,
    south: float,
    east: float,
    west: float,
    frequency: str = "hourly",
    resolution: float = 0.25,
) -> pd.DataFrame:
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
        
    ensure_cdsapi_config()
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}STARTING ERA5 DATA PROCESSING{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    print(f"Variables: {variables}")
    print(
        f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    print(f"Frequency: {frequency}")
    print(f"Resolution: {resolution}°")

    # Validate inputs
    print("\n--- Input Validation ---")
    if not variables:
        raise ValueError("Variables list cannot be empty")
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")
    print(f"{Colors.GREEN}✓ All inputs validated successfully{Colors.RESET}")

    # Get bounding box coordinates
    print("\n--- Calculating Bounding Box ---")
    try:
        west, south, east, north = west, south, east, north
        print(f"{Colors.GREEN}✓ Bounding Box calculated:{Colors.RESET}")
        print(f"  North: {north:.4f}°")
        print(f"  South: {south:.4f}°")
        print(f"  East:  {east:.4f}°")
        print(f"  West:  {west:.4f}°")
        print(f"  Area:  {abs(east-west):.4f}° × {abs(north-south):.4f}°")
    except Exception as e:
        print(f"{Colors.RED}✗ Error calculating bounding box: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Determine processing strategy
    print("\n--- Determining Processing Strategy ---")
    use_monthly = frequency in ["monthly", "yearly"]
    print(f"Using monthly dataset: {use_monthly}")

    if use_monthly:
        max_months_per_chunk = 100
        total_months = (
            (end_date.year - start_date.year) * 12
            + (end_date.month - start_date.month)
            + 1
        )
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
            print(f"{Colors.CYAN}CHUNK {chunk_number}/{total_chunks}{Colors.RESET}")
            print(f"{'='*50}")

            # Calculate chunk end date (last day of the chunk)
            chunk_end_year = current_date.year + (
                (current_date.month - 1 + max_months_per_chunk - 1) // 12
            )
            chunk_end_month = (
                (current_date.month - 1 + max_months_per_chunk - 1) % 12
            ) + 1
            # Last day of chunk_end_month
            next_month = dt.datetime(
                chunk_end_year, chunk_end_month, 28
            ) + dt.timedelta(days=4)
            last_day = next_month - dt.timedelta(days=next_month.day)
            chunk_end = min(last_day, end_date)

            print(
                f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}"
            )

            try:
                print("  → Downloading ERA5 data...")
                download_file = download_with_retry(
                    f"{request_id}_chunk{chunk_number}",
                    variables,
                    current_date,
                    chunk_end,
                    north,
                    west,
                    south,
                    east,
                    resolution,
                    frequency,
                )
                print(f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

                print("  → Extracting files...")
                nc_files = extract_download(download_file)
                print(f"  {Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

                chunk_datasets = []
                print("  → Processing NetCDF files...")
                for i, nc_file in enumerate(nc_files, 1):
                    if not nc_file.lower().endswith(".nc"):
                        print(f"    Skipping non-NetCDF file: {nc_file}")
                        continue
                    try:
                        print(
                            f"    Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                        )
                        ds = xr.open_dataset(nc_file)
                        chunk_datasets.append(ds)
                        print(f"    ✓ Loaded dataset with shape: {dict(ds.dims)}")
                    except Exception as e:
                        print(f"    {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

                if not chunk_datasets:
                    print(f"  {Colors.RED}✗ No datasets were successfully processed for this chunk{Colors.RESET}")
                    chunk_number += 1
                    next_month = chunk_end + dt.timedelta(days=1)
                    current_date = next_month
                    continue

                print("  → Merging datasets...")
                merged_chunk_ds = (
                    xr.merge(chunk_datasets)
                    if len(chunk_datasets) > 1
                    else chunk_datasets[0]
                )
                print(f"  {Colors.GREEN}✓ Merged dataset shape: {dict(merged_chunk_ds.dims)}{Colors.RESET}")

                filtered_chunk_df = merged_chunk_ds.to_dataframe().reset_index()
                print(f"  {Colors.GREEN}✓ Dataframe shape: {filtered_chunk_df.shape}{Colors.RESET}")

                all_filtered_data.append(filtered_chunk_df)

                chunk_time = time.time() - chunk_start_time
                print(f"  {Colors.GREEN}✓ Chunk completed in {chunk_time:.2f} seconds{Colors.RESET}")

            except Exception as e:
                print(
                    f"  {Colors.RED}✗ Error processing chunk {chunk_number}: {e}{Colors.RESET}", file=sys.stderr
                )
                # Continue with next chunk instead of failing completely

            chunk_number += 1
            next_month = chunk_end + dt.timedelta(days=1)
            current_date = next_month

            if chunk_number <= total_chunks:
                print("  → Waiting 10 seconds before next chunk...")
                time.sleep(10)

        if not all_filtered_data:
            print(
                f"{Colors.RED}✗ No data was successfully processed from any chunk{Colors.RESET}", file=sys.stderr
            )
            sys.exit(1)

        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"{Colors.GREEN}✓ Combined data shape: {filtered_df.shape}{Colors.RESET}")

        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(
            subset=["valid_time", "latitude", "longitude"]
        )
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
            print(f"{Colors.CYAN}CHUNK {chunk_number}/{total_chunks}{Colors.RESET}")
            print(f"{'='*50}")

            chunk_end = min(
                current_date + dt.timedelta(days=max_days_per_chunk - 1), end_date
            )
            print(
                f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}"
            )

            try:
                print("  → Downloading ERA5 data...")
                download_file = download_with_retry(
                    f"{request_id}_chunk{chunk_number}",
                    variables,
                    current_date,
                    chunk_end,
                    north,
                    west,
                    south,
                    east,
                    resolution,
                    frequency,
                )
                print(f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

                print("  → Extracting files...")
                nc_files = extract_download(download_file)
                print(f"  {Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

                chunk_datasets = []
                print("  → Processing NetCDF files...")
                for i, nc_file in enumerate(nc_files, 1):
                    if not nc_file.lower().endswith(".nc"):
                        print(f"    Skipping non-NetCDF file: {nc_file}")
                        continue
                    try:
                        print(
                            f"    Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                        )
                        ds = xr.open_dataset(nc_file)
                        chunk_datasets.append(ds)
                        print(f"    ✓ Loaded dataset with shape: {dict(ds.dims)}")
                    except Exception as e:
                        print(f"    {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

                if not chunk_datasets:
                    print(f"  {Colors.RED}✗ No datasets were successfully processed for this chunk{Colors.RESET}")
                    chunk_number += 1
                    current_date = chunk_end + dt.timedelta(days=1)
                    continue

                print("  → Merging datasets...")
                merged_chunk_ds = (
                    xr.merge(chunk_datasets)
                    if len(chunk_datasets) > 1
                    else chunk_datasets[0]
                )
                print(f"  {Colors.GREEN}✓ Merged dataset shape: {dict(merged_chunk_ds.dims)}{Colors.RESET}")

                filtered_chunk_df = merged_chunk_ds.to_dataframe().reset_index()
                print(f"  {Colors.GREEN}✓ Dataframe shape: {filtered_chunk_df.shape}{Colors.RESET}")

                all_filtered_data.append(filtered_chunk_df)

                chunk_time = time.time() - chunk_start_time
                print(f"  {Colors.GREEN}✓ Chunk completed in {chunk_time:.2f} seconds{Colors.RESET}")

            except Exception as e:
                print(
                    f"  {Colors.RED}✗ Error processing chunk {chunk_number}: {e}{Colors.RESET}", file=sys.stderr
                )
                # Continue with next chunk instead of failing completely

            chunk_number += 1
            current_date = chunk_end + dt.timedelta(days=1)

            if chunk_number <= total_chunks:
                print("  → Waiting 10 seconds before next chunk...")
                time.sleep(10)

        if not all_filtered_data:
            print(
                f"{Colors.RED}✗ No data was successfully processed from any chunk{Colors.RESET}", file=sys.stderr
            )
            sys.exit(1)

        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"{Colors.GREEN}✓ Combined data shape: {filtered_df.shape}{Colors.RESET}")

        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(
            subset=["valid_time", "latitude", "longitude"]
        )
        removed_duplicates = initial_rows - len(filtered_df)

    elif not needs_chunking and use_monthly:
        # --- Case 3: Does NOT need chunking, needs monthly dataset ---
        print(f"Processing as a single chunk ({total_months} months)... C3")

        try:
            print("→ Downloading ERA5 data...")
            download_file = download_with_retry(
                request_id,
                variables,
                start_date,
                end_date,
                north,
                west,
                south,
                east,
                resolution,
                frequency,
            )
            print(f"{Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

            print("→ Extracting files...")
            nc_files = extract_download(download_file)
            print(f"{Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

            all_datasets = []
            print("→ Processing NetCDF files...")
            for i, nc_file in enumerate(nc_files, 1):
                if not nc_file.lower().endswith(".nc"):
                    print(f"  Skipping non-NetCDF file: {nc_file}")
                    continue
                try:
                    print(
                        f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                    )
                    ds = xr.open_dataset(nc_file)
                    all_datasets.append(ds)
                    print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")
                except Exception as e:
                    print(f"  {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

            if not all_datasets:
                print(f"{Colors.RED}✗ No datasets were successfully processed{Colors.RESET}", file=sys.stderr)
                sys.exit(1)

            print("→ Merging datasets...")
            merged_ds = (
                xr.merge(all_datasets) if len(all_datasets) > 1 else all_datasets[0]
            )
            print(f"{Colors.GREEN}✓ Merged dataset shape: {dict(merged_ds.dims)}{Colors.RESET}")

            filtered_df = merged_ds.to_dataframe().reset_index()
            print(f"{Colors.GREEN}✓ Dataframe shape: {filtered_df.shape}{Colors.RESET}")

            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(
                subset=["valid_time", "latitude", "longitude"]
            )
            removed_duplicates = initial_rows - len(filtered_df)

        except Exception as e:
            print(f"{Colors.RED}✗ Error in single monthly processing: {e}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

    else:
        # --- Case 4: Does NOT need chunking, does NOT need monthly dataset ---
        print(f"Processing as a single chunk ({total_days} days)... C4")

        try:
            print("→ Downloading ERA5 data...")
            download_file = download_with_retry(
                request_id,
                variables,
                start_date,
                end_date,
                north,
                west,
                south,
                east,
                resolution,
                frequency,
            )
            print(f"{Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

            print("→ Extracting files...")
            nc_files = extract_download(download_file)
            print(f"{Colors.GREEN}✓ Extracted {len(nc_files)} files{Colors.RESET}")

            all_datasets = []
            print("→ Processing NetCDF files...")
            for i, nc_file in enumerate(nc_files, 1):
                if not nc_file.lower().endswith(".nc"):
                    print(f"  Skipping non-NetCDF file: {nc_file}")
                    continue
                try:
                    print(
                        f"  Processing file {i}/{len(nc_files)}: {os.path.basename(nc_file)}"
                    )
                    ds = xr.open_dataset(nc_file)
                    all_datasets.append(ds)
                    print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")
                except Exception as e:
                    print(f"  {Colors.RED}✗ Error processing {nc_file}: {e}{Colors.RESET}", file=sys.stderr)

            if not all_datasets:
                print(f"{Colors.RED}✗ No datasets were successfully processed{Colors.RESET}", file=sys.stderr)
                sys.exit(1)

            print("→ Merging datasets...")
            merged_ds = (
                xr.merge(all_datasets) if len(all_datasets) > 1 else all_datasets[0]
            )
            print(f"{Colors.GREEN}✓ Merged dataset shape: {dict(merged_ds.dims)}{Colors.RESET}")

            filtered_df = merged_ds.to_dataframe().reset_index()
            print(f"{Colors.GREEN}✓ Dataframe shape: {filtered_df.shape}{Colors.RESET}")

            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(
                subset=["valid_time", "latitude", "longitude"]
            )
            removed_duplicates = initial_rows - len(filtered_df)

        except Exception as e:
            print(f"{Colors.RED}✗ Error in single daily processing: {e}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

    # Aggregate by frequency (same for all cases)
    print(f"\n--- Temporal Aggregation ({frequency}) ---")
    try:
        print("→ Performing temporal aggregation...")
        aggregation_start_time = time.time()
        (aggregated_df, unique_latlongs) = aggregate_by_frequency(
            filtered_df, frequency
        )
        aggregation_time = time.time() - aggregation_start_time
        print(f"{Colors.GREEN}✓ Aggregation completed in {aggregation_time:.2f} seconds{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Aggregated data shape: {aggregated_df.shape}{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Unique lat/long combinations: {len(unique_latlongs)}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}✗ Error during aggregation: {e}{Colors.RESET}", file=sys.stderr)
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
        print(f"{Colors.GREEN}✓ Aggregated data exported to: {csv_output}{Colors.RESET}")

        # Save unique lat/longs to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_unique_latlongs.csv")
        unique_latlongs.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Unique lat/longs exported to: {csv_output}{Colors.RESET}")

        # Save raw data to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_raw_data.csv")
        filtered_df.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Raw data exported to: {csv_output}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error saving results: {e}{Colors.RESET}", file=sys.stderr)
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
        print(f"{Colors.BLUE}ERA5 DATA PROCESSING COMPLETED SUCCESSFULLY{Colors.RESET}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Error generating summary statistics: {e}{Colors.RESET}", file=sys.stderr)

    return aggregated_df

def download_pr_with_retry(chunk_id, variables, start_dt, end_dt, north, west, south, east, pressure_levels, resolution, frequency):
    """Helper function to download ERA5 data with retry logic"""
    max_retries = 5
    retry_delay = 30
    for attempt in range(max_retries + 1):
        try:
            print(f"  → Downloading ERA5 data (attempt {attempt + 1}/{max_retries + 1})...")
            download_file = download_era5_pressure_lvl(
                chunk_id,
                variables,
                start_dt,
                end_dt,
                north,
                west,
                south,
                east,
                pressure_levels,
                resolution,
                frequency,
            )
            print(f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")
            return download_file
        except Exception as e:
            error_msg = str(e)
            print(f"  {Colors.RED}✗ Download attempt {attempt + 1} failed: {error_msg}{Colors.RESET}")
                
            # Check if it's a connection-related error
            is_connection_error = any(keyword in error_msg.lower() for keyword in [
                'httpsconnectionpool', 'max retries exceeded', 'connection', 
                'timeout', 'network', 'ssl', 'certificate'
            ])
                
            if attempt < max_retries:
                if is_connection_error:
                    print(f"  {Colors.YELLOW}→ Connection error detected. Retrying in {retry_delay} seconds...{Colors.RESET}")
                else:
                    print(f"  {Colors.YELLOW}→ Error encountered. Retrying in {retry_delay} seconds...{Colors.RESET}")
                time.sleep(retry_delay)
            else:
                print(f"  {Colors.RED}✗ All {max_retries + 1} download attempts failed{Colors.RESET}")
                raise e


def process_era5_pressure_lvl(
    request_id: str,
    variables: List[str],
    start_date: dt.datetime,
    end_date: dt.datetime,
    geojson_file: str,
    pressure_levels: List[str],
    frequency: str = "hourly",
    resolution: float = 0.25,
) -> pd.DataFrame:
    """
    Complete workflow for downloading and processing ERA5 pressure level data.
    Automatically chunks large time range requests for efficient processing.

    Args:
        request_id: Unique identifier for the request
        variables: List of variables to download
        start_date: Start date for data retrieval (datetime object)
        end_date: End date for data retrieval (datetime object)
        geojson_file: Path to the GeoJSON file
        pressure_levels: List of pressure levels to request (hPa as strings)
        frequency: Aggregation frequency ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        resolution: Grid resolution in degrees (default: 0.25°)

    Returns:
        Filtered and aggregated DataFrame with the processed data
    """
    class Colors:
        RESET = "\033[0m"
        RED = "\033[0;31m"
        GREEN = "\033[0;32m"
        YELLOW = "\033[0;33m"
        BLUE = "\033[0;34m"
        PURPLE = "\033[0;35m"
        CYAN = "\033[0;36m"
        WHITE = "\033[0;37m"
        GREEN_BRIGHT = "\033[0;92m"
        RED_BRIGHT = "\033[0;91m"
        YELLOW_BRIGHT = "\033[0;93m"
        BLUE_BRIGHT = "\033[0;94m"
        CYAN_BRIGHT = "\033[0;96m"

    ensure_cdsapi_config()
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}STARTING ERA5 PRESSURE LEVEL PROCESSING{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    print(f"Variables: {variables}")
    print(f"Pressure Levels: {pressure_levels}")
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
    if not pressure_levels:
        raise ValueError("Pressure levels list cannot be empty")
    print(f"{Colors.GREEN}✓ All inputs validated successfully{Colors.RESET}")

    # Load GeoJSON file
    print("\n--- Loading GeoJSON File ---")
    try:
        geojson_data = load_json_with_encoding(geojson_file)
        if not is_valid_geojson(geojson_data):
            geojson_data = convert_to_geojson(geojson_data)
        print(f"{Colors.GREEN}✓ GeoJSON loaded successfully{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}✗ Error loading GeoJSON file: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Get bounding box coordinates
    print("\n--- Calculating Bounding Box ---")
    try:
        west, south, east, north = get_bounding_box(geojson_data)
        print(f"{Colors.GREEN}✓ Bounding Box calculated:{Colors.RESET}")
        print(f"  North: {north:.4f}°")
        print(f"  South: {south:.4f}°")
        print(f"  East:  {east:.4f}°")
        print(f"  West:  {west:.4f}°")
        print(f"  Area:  {abs(east-west):.4f}° × {abs(north-south):.4f}°")
    except Exception as e:
        print(f"{Colors.RED}✗ Error calculating bounding box: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Determine processing strategy
    print("\n--- Determining Processing Strategy ---")
    use_monthly = frequency in ["monthly", "yearly"]
    print(f"Using monthly dataset: {use_monthly}")

    if use_monthly:
        max_months_per_chunk = 100
        total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        needs_chunking = total_months > max_months_per_chunk
    else:
        max_days_per_chunk = 14
        total_days = (end_date - start_date).days + 1
        needs_chunking = total_days > max_days_per_chunk

    print(f"Total {'months' if use_monthly else 'days'} to process: {total_months if use_monthly else total_days}")
    print(f"Max {'months' if use_monthly else 'days'} per chunk: {max_months_per_chunk if use_monthly else max_days_per_chunk}")
    print(f"Needs chunking: {needs_chunking}")

    all_filtered_data = []
    processing_start_time = time.time()

    if needs_chunking:
        # Chunked processing
        current_date = start_date
        chunk_number = 1
        total_chunks = math.ceil(total_months / max_months_per_chunk) if use_monthly else math.ceil(total_days / max_days_per_chunk)

        while current_date <= end_date:
            chunk_start_time = time.time()
            print(f"\n{'='*50}")
            print(f"{Colors.CYAN}CHUNK {chunk_number}/{total_chunks}{Colors.RESET}")
            print(f"{'='*50}")

            # Calculate chunk end date
            if use_monthly:
                chunk_end_year = current_date.year + ((current_date.month - 1 + max_months_per_chunk - 1) // 12)
                chunk_end_month = ((current_date.month - 1 + max_months_per_chunk - 1) % 12) + 1
                next_month = dt.datetime(chunk_end_year, chunk_end_month, 28) + dt.timedelta(days=4)
                chunk_end = min(next_month - dt.timedelta(days=next_month.day), end_date)
            else:
                chunk_end = min(current_date + dt.timedelta(days=max_days_per_chunk - 1), end_date)

            print(f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")

            try:
                # Download data for this chunk
                print("  → Downloading ERA5 pressure level data...")
                download_file = download_pr_with_retry(
                    f"{request_id}_chunk{chunk_number}",
                    variables,
                    current_date,
                    chunk_end,
                    north,
                    west,
                    south,
                    east,
                    pressure_levels,
                    resolution,
                    frequency
                )
                print(f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

                # Process the downloaded file
                print("  → Processing NetCDF file...")
                ds = xr.open_dataset(download_file)
                print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")

                # Filter by shapefile
                print("  → Filtering by shapefile...")
                filtered_chunk_df = filter_netcdf_by_shapefile(ds, geojson_data)
                print(f"  {Colors.GREEN}✓ Filtered data shape: {filtered_chunk_df.shape}{Colors.RESET}")

                all_filtered_data.append(filtered_chunk_df)

                chunk_time = time.time() - chunk_start_time
                print(f"  {Colors.GREEN}✓ Chunk completed in {chunk_time:.2f} seconds{Colors.RESET}")

            except Exception as e:
                print(f"  {Colors.RED}✗ Error processing chunk {chunk_number}: {e}{Colors.RESET}", file=sys.stderr)

            # Prepare for next chunk
            chunk_number += 1
            current_date = chunk_end + dt.timedelta(days=1)
            
            if chunk_number <= total_chunks:
                print("  → Waiting 10 seconds before next chunk...")
                time.sleep(10)

        if not all_filtered_data:
            print(f"{Colors.RED}✗ No data was successfully processed from any chunk{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

        # Combine all chunks
        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"{Colors.GREEN}✓ Combined data shape: {filtered_df.shape}{Colors.RESET}")

        # Remove duplicates
        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(subset=["valid_time", "latitude", "longitude", "pressure_level"])
        removed_duplicates = initial_rows - len(filtered_df)
        if removed_duplicates > 0:
            print(f"{Colors.YELLOW}✓ Removed {removed_duplicates} duplicate rows{Colors.RESET}")

    else:
        # Single chunk processing
        print(f"Processing as a single chunk ({total_months if use_monthly else total_days} {'months' if use_monthly else 'days'})...")

        try:
            # Download all data at once
            print("→ Downloading ERA5 pressure level data...")
            download_file = download_pr_with_retry(
                request_id,
                variables,
                start_date,
                end_date,
                north,
                west,
                south,
                east,
                pressure_levels,
                resolution,
                frequency
            )
            print(f"{Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

            # Process the downloaded file
            print("→ Processing NetCDF file...")
            ds = xr.open_dataset(download_file)
            print(f"✓ Loaded dataset with shape: {dict(ds.dims)}")

            # Filter by shapefile
            print("→ Filtering by shapefile...")
            filtered_df = filter_netcdf_by_shapefile(ds, geojson_data)
            print(f"{Colors.GREEN}✓ Filtered data shape: {filtered_df.shape}{Colors.RESET}")

            # Remove duplicates
            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(subset=["valid_time", "latitude", "longitude", "pressure_level"])
            removed_duplicates = initial_rows - len(filtered_df)
            if removed_duplicates > 0:
                print(f"{Colors.YELLOW}✓ Removed {removed_duplicates} duplicate rows{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}✗ Error in processing: {e}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

    # Aggregate by frequency
    print(f"\n--- Temporal Aggregation ({frequency}) ---")
    try:
        print("→ Performing temporal aggregation...")
        aggregation_start_time = time.time()
        (aggregated_df, unique_latlongs) = aggregate_pressure_levels(filtered_df, frequency)
        aggregation_time = time.time() - aggregation_start_time
        #debuggin op
        print(aggregated_df)
        print(f"{Colors.GREEN}✓ Aggregation completed in {aggregation_time:.2f} seconds{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Aggregated data shape: {aggregated_df.shape}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}✗ Error during aggregation: {e}{Colors.RESET}", file=sys.stderr)
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
        print(f"{Colors.GREEN}✓ Aggregated data exported to: {csv_output}{Colors.RESET}")

        # Save unique lat/longs to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_unique_latlongs.csv")
        unique_latlongs.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Unique lat/longs exported to: {csv_output}{Colors.RESET}")

        # Save raw data to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_raw_data.csv")
        filtered_df.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Raw data exported to: {csv_output}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error saving results: {e}{Colors.RESET}", file=sys.stderr)

    # Final summary
    print(f"\n--- Summary Statistics ---")
    total_processing_time = time.time() - processing_start_time
    print(f"Total processing time: {total_processing_time:.2f} seconds")
    print(f"Final dataset shape: {aggregated_df.shape}")

    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}ERA5 PRESSURE LEVEL PROCESSING COMPLETED SUCCESSFULLY{Colors.RESET}")
    print(f"{'='*60}")

    return aggregated_df

def process_era5_pressure_lvl_no_filter(
    request_id: str,
    variables: List[str],
    start_date: dt.datetime,
    end_date: dt.datetime,
    north: float,
    south: float,
    east: float,
    west: float,
    pressure_levels: List[str],
    frequency: str = "hourly",
    resolution: float = 0.25,
) -> pd.DataFrame:
    """
    Complete workflow for downloading and processing ERA5 pressure level data.
    Automatically chunks large time range requests for efficient processing.

    Args:
        request_id: Unique identifier for the request
        variables: List of variables to download
        start_date: Start date for data retrieval (datetime object)
        end_date: End date for data retrieval (datetime object)
        geojson_file: Path to the GeoJSON file
        pressure_levels: List of pressure levels to request (hPa as strings)
        frequency: Aggregation frequency ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        resolution: Grid resolution in degrees (default: 0.25°)

    Returns:
        Filtered and aggregated DataFrame with the processed data
    """
    class Colors:
        RESET = "\033[0m"
        RED = "\033[0;31m"
        GREEN = "\033[0;32m"
        YELLOW = "\033[0;33m"
        BLUE = "\033[0;34m"
        PURPLE = "\033[0;35m"
        CYAN = "\033[0;36m"
        WHITE = "\033[0;37m"
        GREEN_BRIGHT = "\033[0;92m"
        RED_BRIGHT = "\033[0;91m"
        YELLOW_BRIGHT = "\033[0;93m"
        BLUE_BRIGHT = "\033[0;94m"
        CYAN_BRIGHT = "\033[0;96m"

    ensure_cdsapi_config()
    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}STARTING ERA5 PRESSURE LEVEL PROCESSING{Colors.RESET}")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    print(f"Variables: {variables}")
    print(f"Pressure Levels: {pressure_levels}")
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Frequency: {frequency}")
    print(f"Resolution: {resolution}°")

    # Validate inputs
    print("\n--- Input Validation ---")
    if not variables:
        raise ValueError("Variables list cannot be empty")
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")
    if not pressure_levels:
        raise ValueError("Pressure levels list cannot be empty")
    print(f"{Colors.GREEN}✓ All inputs validated successfully{Colors.RESET}")

    # Get bounding box coordinates
    print("\n--- Calculating Bounding Box ---")
    try:
        west, south, east, north = west, south, east, north
        print(f"{Colors.GREEN}✓ Bounding Box calculated:{Colors.RESET}")
        print(f"  North: {north:.4f}°")
        print(f"  South: {south:.4f}°")
        print(f"  East:  {east:.4f}°")
        print(f"  West:  {west:.4f}°")
        print(f"  Area:  {abs(east-west):.4f}° × {abs(north-south):.4f}°")
    except Exception as e:
        print(f"{Colors.RED}✗ Error calculating bounding box: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Determine processing strategy
    print("\n--- Determining Processing Strategy ---")
    use_monthly = frequency in ["monthly", "yearly"]
    print(f"Using monthly dataset: {use_monthly}")

    if use_monthly:
        max_months_per_chunk = 100
        total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        needs_chunking = total_months > max_months_per_chunk
    else:
        max_days_per_chunk = 14
        total_days = (end_date - start_date).days + 1
        needs_chunking = total_days > max_days_per_chunk

    print(f"Total {'months' if use_monthly else 'days'} to process: {total_months if use_monthly else total_days}")
    print(f"Max {'months' if use_monthly else 'days'} per chunk: {max_months_per_chunk if use_monthly else max_days_per_chunk}")
    print(f"Needs chunking: {needs_chunking}")

    all_filtered_data = []
    processing_start_time = time.time()

    if needs_chunking:
        # Chunked processing
        current_date = start_date
        chunk_number = 1
        total_chunks = math.ceil(total_months / max_months_per_chunk) if use_monthly else math.ceil(total_days / max_days_per_chunk)

        while current_date <= end_date:
            chunk_start_time = time.time()
            print(f"\n{'='*50}")
            print(f"{Colors.CYAN}CHUNK {chunk_number}/{total_chunks}{Colors.RESET}")
            print(f"{'='*50}")

            # Calculate chunk end date
            if use_monthly:
                chunk_end_year = current_date.year + ((current_date.month - 1 + max_months_per_chunk - 1) // 12)
                chunk_end_month = ((current_date.month - 1 + max_months_per_chunk - 1) % 12) + 1
                next_month = dt.datetime(chunk_end_year, chunk_end_month, 28) + dt.timedelta(days=4)
                chunk_end = min(next_month - dt.timedelta(days=next_month.day), end_date)
            else:
                chunk_end = min(current_date + dt.timedelta(days=max_days_per_chunk - 1), end_date)

            print(f"Processing: {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")

            try:
                # Download data for this chunk
                print("  → Downloading ERA5 pressure level data...")
                download_file = download_pr_with_retry(
                    f"{request_id}_chunk{chunk_number}",
                    variables,
                    current_date,
                    chunk_end,
                    north,
                    west,
                    south,
                    east,
                    pressure_levels,
                    resolution,
                    frequency
                )
                print(f"  {Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

                # Process the downloaded file
                print("  → Processing NetCDF file...")
                ds = xr.open_dataset(download_file)
                print(f"  ✓ Loaded dataset with shape: {dict(ds.dims)}")

                filtered_chunk_df = ds.to_dataframe().reset_index()
                print(f"  {Colors.GREEN}✓ Dataframe shape: {filtered_chunk_df.shape}{Colors.RESET}")

                all_filtered_data.append(filtered_chunk_df)

                chunk_time = time.time() - chunk_start_time
                print(f"  {Colors.GREEN}✓ Chunk completed in {chunk_time:.2f} seconds{Colors.RESET}")

            except Exception as e:
                print(f"  {Colors.RED}✗ Error processing chunk {chunk_number}: {e}{Colors.RESET}", file=sys.stderr)

            # Prepare for next chunk
            chunk_number += 1
            current_date = chunk_end + dt.timedelta(days=1)
            
            if chunk_number <= total_chunks:
                print("  → Waiting 10 seconds before next chunk...")
                time.sleep(10)

        if not all_filtered_data:
            print(f"{Colors.RED}✗ No data was successfully processed from any chunk{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

        # Combine all chunks
        print("\n--- Combining Chunk Results ---")
        filtered_df = pd.concat(all_filtered_data, ignore_index=True)
        print(f"{Colors.GREEN}✓ Combined data shape: {filtered_df.shape}{Colors.RESET}")

        # Remove duplicates
        initial_rows = len(filtered_df)
        filtered_df = filtered_df.drop_duplicates(subset=["valid_time", "latitude", "longitude", "pressure_level"])
        removed_duplicates = initial_rows - len(filtered_df)
        if removed_duplicates > 0:
            print(f"{Colors.YELLOW}✓ Removed {removed_duplicates} duplicate rows{Colors.RESET}")

    else:
        # Single chunk processing
        print(f"Processing as a single chunk ({total_months if use_monthly else total_days} {'months' if use_monthly else 'days'})...")

        try:
            # Download all data at once
            print("→ Downloading ERA5 pressure level data...")
            download_file = download_pr_with_retry(
                request_id,
                variables,
                start_date,
                end_date,
                north,
                west,
                south,
                east,
                pressure_levels,
                resolution,
                frequency
            )
            print(f"{Colors.GREEN}✓ Download completed: {download_file}{Colors.RESET}")

            # Process the downloaded file
            print("→ Processing NetCDF file...")
            ds = xr.open_dataset(download_file)
            print(f"✓ Loaded dataset with shape: {dict(ds.dims)}")

            filtered_df = ds.to_dataframe().reset_index()
            print(f"{Colors.GREEN}✓ Dataframe shape: {filtered_df.shape}{Colors.RESET}")

            # Remove duplicates
            initial_rows = len(filtered_df)
            filtered_df = filtered_df.drop_duplicates(subset=["valid_time", "latitude", "longitude", "pressure_level"])
            removed_duplicates = initial_rows - len(filtered_df)
            if removed_duplicates > 0:
                print(f"{Colors.YELLOW}✓ Removed {removed_duplicates} duplicate rows{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}✗ Error in processing: {e}{Colors.RESET}", file=sys.stderr)
            sys.exit(1)

    # Aggregate by frequency
    print(f"\n--- Temporal Aggregation ({frequency}) ---")
    try:
        print("→ Performing temporal aggregation...")
        aggregation_start_time = time.time()
        (aggregated_df, unique_latlongs) = aggregate_pressure_levels(filtered_df, frequency)
        aggregation_time = time.time() - aggregation_start_time
        #debuggin op
        print(aggregated_df)
        print(f"{Colors.GREEN}✓ Aggregation completed in {aggregation_time:.2f} seconds{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Aggregated data shape: {aggregated_df.shape}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}✗ Error during aggregation: {e}{Colors.RESET}", file=sys.stderr)
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
        print(f"{Colors.GREEN}✓ Aggregated data exported to: {csv_output}{Colors.RESET}")

        # Save unique lat/longs to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_unique_latlongs.csv")
        unique_latlongs.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Unique lat/longs exported to: {csv_output}{Colors.RESET}")

        # Save raw data to CSV
        csv_output = os.path.join(output_dir, f"{request_id}_raw_data.csv")
        filtered_df.to_csv(csv_output, index=False)
        print(f"{Colors.GREEN}✓ Raw data exported to: {csv_output}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}✗ Error saving results: {e}{Colors.RESET}", file=sys.stderr)

    # Final summary
    print(f"\n--- Summary Statistics ---")
    total_processing_time = time.time() - processing_start_time
    print(f"Total processing time: {total_processing_time:.2f} seconds")
    print(f"Final dataset shape: {aggregated_df.shape}")

    print(f"\n{'='*60}")
    print(f"{Colors.BLUE}ERA5 PRESSURE LEVEL PROCESSING COMPLETED SUCCESSFULLY{Colors.RESET}")
    print(f"{'='*60}")

    return aggregated_df

import json
import os
import datetime as dt
from typing import List
import pandas as pd

def era5ify_geojson(
    request_id: str,
    variables: List[str],
    start_date: str,
    end_date: str,
    json_file: str,
    dataset_type: str = "single",  # "single" or "pressure"
    pressure_levels: Optional[List[str]] = None,
    frequency: str = "hourly",
    resolution: float = 0.25,
) -> pd.DataFrame:
    """
    Wrapper function that handles different JSON formats before processing ERA5 data.
    Supports both single-level and pressure-level datasets.

    Args:
        request_id: Unique identifier for the request
        variables: List of variables to download
        start_date: Start date for data retrieval (datetime object)
        end_date: End date for data retrieval (datetime object)
        json_file: Path to the JSON or GeoJSON file
        dataset_type: Type of ERA5 data ("single" or "pressure")
        pressure_levels: List of pressure levels (required for "pressure" type)
        frequency: Aggregation frequency ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        resolution: Grid resolution in degrees (default: 0.25°)

    Returns:
        Filtered and aggregated DataFrame with the processed data

    Raises:
        ValueError: If invalid dataset_type or missing pressure_levels for pressure data
    """
    
    try:
        parts = start_date.split('-')
        if len(parts) == 3:
            start_dt = dt.datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            raise ValueError
    except (ValueError, IndexError):
        raise ValueError(f"Invalid start_date format: {start_date}. Expected 'YYYY-M-D' or 'YYYY-MM-DD'")
    
    try:
        parts = end_date.split('-')
        if len(parts) == 3:
            end_dt = dt.datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            raise ValueError
    except (ValueError, IndexError):
        raise ValueError(f"Invalid end_date format: {end_date}. Expected 'YYYY-M-D' or 'YYYY-MM-DD'")

    # Validate dataset type
    dataset_type = dataset_type.lower()
    if dataset_type not in ["single", "pressure"]:
        raise ValueError(f"Invalid dataset_type: {dataset_type}. Must be 'single' or 'pressure'")

    # Validate pressure levels if needed
    if dataset_type == "pressure" and not pressure_levels:
        raise ValueError("pressure_levels must be provided for pressure level data")

    # Handle different file encodings
    json_data = load_json_with_encoding(json_file)

    # Check if it's valid GeoJSON
    if is_valid_geojson(json_data):
        print(f"Valid GeoJSON detected: {json_file}")
        geojson_data = json_data
    else:
        print(f"Converting JSON to GeoJSON format...")
        geojson_data = convert_to_geojson(json_data)

    # Create temporary GeoJSON file (even if original was valid, for consistent processing)
    temp_geojson_file = create_temp_geojson(geojson_data, request_id)
    print(f"Using GeoJSON file: {temp_geojson_file}")

    try:
        # Route to appropriate processor
        if dataset_type == "pressure":
            return process_era5_pressure_lvl(
                request_id=request_id,
                variables=variables,
                start_date=start_dt,
                end_date=end_dt,
                geojson_file=temp_geojson_file,
                pressure_levels=pressure_levels,
                frequency=frequency,
                resolution=resolution
            )
        else:
            return process_era5_single_lvl(
                request_id=request_id,
                variables=variables,
                start_date=start_dt,
                end_date=end_dt,
                geojson_file=temp_geojson_file,
                frequency=frequency,
                resolution=resolution
            )
    finally:
        # Clean up temporary files
        if os.path.exists(temp_geojson_file) and temp_geojson_file != json_file:
            print(f"Removing temporary GeoJSON file: {temp_geojson_file}")
            os.remove(temp_geojson_file)
        temp_dir = tempfile.gettempdir()
        zip_pattern = os.path.join(temp_dir, f"*{request_id}*.zip")
        for zip_file in glob.glob(zip_pattern):
            if os.path.exists(zip_file):
                print(f"Removing ERA5 zip file: {zip_file}")
                os.remove(zip_file)
        dir_pattern = os.path.join(temp_dir, f"*{request_id}*")
        for item in glob.glob(dir_pattern):
            if os.path.isdir(item):
                print(f"Removing extraction directory: {item}")
                shutil.rmtree(item)

def era5ify_bbox(
    request_id: str, 
    variables: List[str], 
    start_date: str,
    end_date: str,
    north: float,
    south: float,
    east: float,
    west: float,
    dataset_type: str = "single",  # "single" or "pressure"
    pressure_levels: Optional[List[str]] = None,
    frequency: str = 'hourly',
    resolution: float = 0.25
) -> pd.DataFrame:
    """
    Process ERA5 data for a specified bounding box without requiring a GeoJSON file.
    Supports both single-level and pressure-level datasets.

    Args:
        request_id: Unique identifier for the request
        variables: List of variables to download
        start_date: Start date for data retrieval (datetime object)
        end_date: End date for data retrieval (datetime object)
        north: Northern latitude boundary
        south: Southern latitude boundary
        east: Eastern longitude boundary
        west: Western longitude boundary
        dataset_type: Type of ERA5 data ("single" or "pressure")
        pressure_levels: List of pressure levels (required for "pressure" type)
        frequency: Aggregation frequency ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        resolution: Grid resolution in degrees (default: 0.25°)

    Returns:
        Filtered and aggregated DataFrame with the processed data

    Raises:
        ValueError: If bounding box coordinates are invalid or missing pressure levels for pressure data
    """
    
    try:
        parts = start_date.split('-')
        if len(parts) == 3:
            start_dt = dt.datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            raise ValueError
    except (ValueError, IndexError):
        raise ValueError(f"Invalid start_date format: {start_date}. Expected 'YYYY-M-D' or 'YYYY-MM-DD'")
    
    try:
        parts = end_date.split('-')
        if len(parts) == 3:
            end_dt = dt.datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            raise ValueError
    except (ValueError, IndexError):
        raise ValueError(f"Invalid end_date format: {end_date}. Expected 'YYYY-M-D' or 'YYYY-MM-DD'")

    # Validate dataset type
    dataset_type = dataset_type.lower()
    if dataset_type not in ["single", "pressure"]:
        raise ValueError(f"Invalid dataset_type: {dataset_type}. Must be 'single' or 'pressure'")

    # Validate pressure levels if needed
    if dataset_type == "pressure" and not pressure_levels:
        raise ValueError("pressure_levels must be provided for pressure level data")

    print(f"\n{'='*60}")
    print(f"STARTING ERA5 {dataset_type.upper()} LEVEL BBOX PROCESSING")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    print(f"Variables: {variables}")
    if dataset_type == "pressure":
        print(f"Pressure Levels: {pressure_levels}")
    print(f"Date Range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
    print(f"Bounding Box: N:{north}, S:{south}, E:{east}, W:{west}")
    print(f"Frequency: {frequency}")
    print(f"Resolution: {resolution}°")

    # Validate bounding box coordinates
    print("\n--- Bounding Box Validation ---")
    if north <= south:
        raise ValueError(f"North ({north}) must be greater than South ({south})")
    if east <= west:
        raise ValueError(f"East ({east}) must be greater than West ({west})")
    if not (-90 <= south <= 90) or not (-90 <= north <= 90):
        raise ValueError(f"Latitude values must be between -90 and 90. Got North: {north}, South: {south}")
    if not (-180 <= west <= 180) or not (-180 <= east <= 180):
        raise ValueError(f"Longitude values must be between -180 and 180. Got East: {east}, West: {west}")
    
    print("✓ Bounding box coordinates validated successfully")
    print(f"  Area: {abs(east-west):.4f}° × {abs(north-south):.4f}°")

    # Create GeoJSON from bounding box coordinates
    print("\n--- Creating GeoJSON from Bounding Box ---")
    geojson_data = create_geojson_from_bbox(west, south, east, north)
    print("✓ GeoJSON created successfully")

    # Create temporary GeoJSON file
    temp_geojson_file = create_temp_geojson(geojson_data, request_id)
    print(f"✓ Created temporary GeoJSON file: {temp_geojson_file}")

    try:
        # Route to appropriate processor
        if dataset_type == "pressure":
            result_df = process_era5_pressure_lvl_no_filter(
                request_id=request_id,
                variables=variables,
                start_date=start_dt,
                end_date=end_dt,
                north=north,
                south=south,
                east=east,
                west=west,
                pressure_levels=pressure_levels,
                frequency=frequency,
                resolution=resolution
            )
        else:
            result_df = process_era5_single_lvl_no_filter(
                request_id=request_id,
                variables=variables,
                start_date=start_dt,
                end_date=end_dt,
                north=north,
                south=south,
                east=east,
                west=west,
                frequency=frequency,
                resolution=resolution
            )

        print(f"\n{'='*60}")
        print(f"ERA5 {dataset_type.upper()} LEVEL BBOX PROCESSING COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")

        return result_df

    finally:
        # Clean up temporary files
        if os.path.exists(temp_geojson_file):
            print(f"\n--- Cleanup ---")
            print(f"Removing temporary GeoJSON file: {temp_geojson_file}")
            os.remove(temp_geojson_file)
            print("✓ Cleanup completed")
        temp_dir = tempfile.gettempdir()
        zip_pattern = os.path.join(temp_dir, f"*{request_id}*.zip")
        for zip_file in glob.glob(zip_pattern):
            if os.path.exists(zip_file):
                print(f"Removing ERA5 zip file: {zip_file}")
                os.remove(zip_file)
        nc_pattern = os.path.join(temp_dir, f"*{request_id}*.nc")
        for nc_file in glob.glob(nc_pattern):
            if os.path.exists(nc_file):
                print(f"Removing ERA5 nc file: {nc_file}")
                os.remove(nc_file)
        dir_pattern = os.path.join(temp_dir, f"*{request_id}*")
        for item in glob.glob(dir_pattern):
            if os.path.isdir(item):
                print(f"Removing extraction directory: {item}")
                shutil.rmtree(item)