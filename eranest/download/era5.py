"""
Optimized ERA5 data download functionality.

This module provides efficient and robust downloading of ERA5 data
from ECMWF's Climate Data Store with proper error handling and optimization.
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import cdsapi
import pandas as pd

from ..config import ensure_cdsapi_config
from ..constants import (
    AURORA_PRESSURE_LEVELS,
    DEFAULT_ATMOSPHERIC_VARIABLES,
    DEFAULT_RESOLUTION,
    DEFAULT_STATIC_VARIABLES,
    DEFAULT_SURFACE_VARIABLES,
    ERA5_DATASETS,
    DataFrequency,
    DatasetType,
)
from ..exceptions import (
    ConfigurationError,
    DataDownloadError,
    NetworkError,
    ValidationError,
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class DownloadRequest:
    """Represents a download request with all necessary parameters."""

    request_id: str
    variables: List[str]
    start_date: datetime
    end_date: datetime
    north: float
    west: float
    south: float
    east: float
    dataset_type: DatasetType
    frequency: DataFrequency = DataFrequency.HOURLY
    resolution: float = DEFAULT_RESOLUTION
    pressure_levels: Optional[List[str]] = None
    output_dir: Optional[str] = None

    def __post_init__(self):
        """Validate the download request after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all parameters of the download request."""
        if self.start_date > self.end_date:
            raise ValidationError("Start date must be before end date")

        if not (-90 <= self.south <= self.north <= 90):
            raise ValidationError("Invalid latitude range")

        if not (-180 <= self.west <= self.east <= 360):
            raise ValidationError("Invalid longitude range")

        if not self.variables:
            raise ValidationError("At least one variable must be specified")

        if self.dataset_type == DatasetType.PRESSURE and not self.pressure_levels:
            raise ValidationError("Pressure levels required for atmospheric data")


class ERA5Downloader:
    """
    Optimized ERA5 data downloader with caching and error recovery.

    This class provides a high-level interface for downloading ERA5 data
    with built-in optimization, error handling, and progress tracking.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        parallel_downloads: bool = False,
        max_workers: int = 2,
    ):
        """
        Initialize the ERA5 downloader.

        Args:
            max_retries: Maximum number of retry attempts for failed downloads
            retry_delay: Delay between retry attempts in seconds
            parallel_downloads: Whether to enable parallel downloads
            max_workers: Maximum number of parallel download workers
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.parallel_downloads = parallel_downloads
        self.max_workers = max_workers
        self._client = None

        # Ensure CDS API is configured
        ensure_cdsapi_config()

    @property
    def client(self) -> cdsapi.Client:
        """Lazy initialization of CDS API client."""
        if self._client is None:
            try:
                self._client = cdsapi.Client()
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize CDS API client: {e}")
        return self._client

    def download(self, request: DownloadRequest) -> str:
        """
        Download ERA5 data based on the provided request.

        Args:
            request: DownloadRequest object with all necessary parameters

        Returns:
            Path to the downloaded file

        Raises:
            DataDownloadError: If download fails after all retries
        """
        logger.info(f"Starting download for request: {request.request_id}")

        # Prepare download parameters
        download_params = self._prepare_download_params(request)
        output_file = self._get_output_filename(request)

        # Attempt download with retries
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Download attempt {attempt + 1}/{self.max_retries + 1}")

                # Execute the download
                self.client.retrieve(
                    download_params["dataset"], download_params["request"], output_file
                )

                # Verify the downloaded file
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    logger.info(f"Download completed successfully: {output_file}")
                    return output_file
                else:
                    raise DataDownloadError("Downloaded file is empty or missing")

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    raise DataDownloadError(
                        f"Download failed after {self.max_retries + 1} attempts: {e}"
                    )

    def download_multiple(self, requests: List[DownloadRequest]) -> List[str]:
        """
        Download multiple ERA5 datasets efficiently.

        Args:
            requests: List of download requests

        Returns:
            List of paths to downloaded files
        """
        if not self.parallel_downloads or len(requests) == 1:
            # Sequential download
            return [self.download(request) for request in requests]

        # Parallel download
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_request = {
                executor.submit(self.download, request): request for request in requests
            }

            for future in as_completed(future_to_request):
                request = future_to_request[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed download for {request.request_id}")
                except Exception as e:
                    logger.error(f"Failed download for {request.request_id}: {e}")
                    raise

        return results

    def _prepare_download_params(self, request: DownloadRequest) -> Dict[str, Any]:
        """Prepare download parameters for CDS API call."""

        # Select appropriate dataset
        if request.dataset_type == DatasetType.STATIC:
            dataset = ERA5_DATASETS["surface"]["hourly"]  # Static uses surface dataset
        else:
            dataset_key = (
                "pressure"
                if request.dataset_type == DatasetType.PRESSURE
                else "surface"
            )
            freq_key = (
                "monthly" if request.frequency == DataFrequency.MONTHLY else "hourly"
            )
            dataset = ERA5_DATASETS[dataset_key][freq_key]

        # Prepare time parameters
        date_params = self._prepare_date_params(request)

        # Base request parameters
        api_request = {
            "product_type": (
                "reanalysis"
                if request.frequency != DataFrequency.MONTHLY
                else "monthly_averaged_reanalysis"
            ),
            "variable": request.variables,
            "area": [request.north, request.west, request.south, request.east],
            "format": "netcdf",
            "grid": [request.resolution, request.resolution],
            **date_params,
        }

        # Add pressure levels for atmospheric data
        if request.dataset_type == DatasetType.PRESSURE and request.pressure_levels:
            api_request["pressure_level"] = request.pressure_levels

        # Add time parameters for non-static data
        if request.dataset_type != DatasetType.STATIC:
            if request.frequency == DataFrequency.MONTHLY:
                api_request["time"] = ["00:00"]
            else:
                api_request["time"] = [f"{h:02d}:00" for h in range(24)]
        else:
            # For static data, use a single time point
            api_request["time"] = "00:00"

        return {
            "dataset": dataset,
            "request": api_request,
        }

    def _prepare_date_params(self, request: DownloadRequest) -> Dict[str, List[str]]:
        """Prepare date parameters for the API request."""
        if request.dataset_type == DatasetType.STATIC:
            # Static data only needs a single date
            return {
                "year": ["2023"],
                "month": ["01"],
                "day": ["01"],
            }

        # Generate date ranges for time-varying data
        date_params = {"year": [], "month": [], "day": []}
        current_date = request.start_date

        while current_date <= request.end_date:
            year = str(current_date.year)
            month = f"{current_date.month:02d}"
            day = f"{current_date.day:02d}"

            if year not in date_params["year"]:
                date_params["year"].append(year)
            if month not in date_params["month"]:
                date_params["month"].append(month)
            if day not in date_params["day"]:
                date_params["day"].append(day)

            current_date += timedelta(days=1)

        return date_params

    def _get_output_filename(self, request: DownloadRequest) -> str:
        """Generate output filename for the download."""
        output_dir = request.output_dir or "."
        os.makedirs(output_dir, exist_ok=True)

        type_suffix = {
            DatasetType.SURFACE: "surface",
            DatasetType.PRESSURE: "atmospheric",
            DatasetType.STATIC: "static",
        }[request.dataset_type]

        filename = f"{request.request_id}_{type_suffix}.nc"
        return os.path.join(output_dir, filename)


# Convenience functions for common download operations


def download_surface_data(
    request_id: str,
    variables: Optional[List[str]] = None,
    start_date: Optional[Union[str, datetime]] = None,
    end_date: Optional[Union[str, datetime]] = None,
    north: Optional[float] = None,
    west: Optional[float] = None,
    south: Optional[float] = None,
    east: Optional[float] = None,
    geometry: Optional[Union[str, Dict]] = None,
    frequency: Union[str, DataFrequency] = DataFrequency.HOURLY,
    resolution: float = DEFAULT_RESOLUTION,
    verbose: bool = False,
    show_progress: bool = True,
    **kwargs,
) -> str:
    """
    Download surface-level ERA5 data.

    Args:
        request_id: Unique identifier for the request
        variables: List of surface variables (defaults to DEFAULT_SURFACE_VARIABLES)
        start_date: Start date for data retrieval (string or datetime)
        end_date: End date for data retrieval (string or datetime)
        north, west, south, east: Bounding box coordinates (optional if geometry provided)
        geometry: Path to GeoJSON file or geometry dict (alternative to bbox)
        frequency: Data frequency
        resolution: Grid resolution in degrees
        verbose: Enable verbose logging
        show_progress: Show progress bar for downloads
        **kwargs: Additional arguments for ERA5Downloader

    Returns:
        Path to the downloaded file
    """
    from ..utils.validation import parse_date, extract_bbox_from_geometry
    from ..utils.io import load_json_file
    from .. import set_verbosity, _is_notebook
    
    # Handle verbosity
    if verbose:
        set_verbosity('INFO')
    
    # Check if we're in a notebook for progress bars
    in_notebook = _is_notebook()
    
    if show_progress and in_notebook:
        try:
            from tqdm.notebook import tqdm
            progress = tqdm(total=3, desc="Downloading surface data")
        except ImportError:
            from tqdm import tqdm
            progress = tqdm(total=3, desc="Downloading surface data")
    elif show_progress:
        try:
            from tqdm import tqdm
            progress = tqdm(total=3, desc="Downloading surface data")
        except ImportError:
            progress = None
    else:
        progress = None
    
    try:
        # Step 1: Parse parameters
        if progress:
            progress.set_description("Parsing parameters")
            progress.update(1)
        
        # Set defaults
        variables = variables or DEFAULT_SURFACE_VARIABLES
        start_date = parse_date(start_date) if start_date else datetime(2024, 1, 1)
        end_date = parse_date(end_date) if end_date else datetime(2024, 1, 2)

        # Handle geometry vs bounding box
        if geometry:
            if isinstance(geometry, str):
                geometry_data = load_json_file(geometry)
            else:
                geometry_data = geometry
            north, west, south, east = extract_bbox_from_geometry(geometry_data)
        else:
            # Use provided bbox or defaults
            north = north if north is not None else 90.0
            west = west if west is not None else -180.0
            south = south if south is not None else -90.0
            east = east if east is not None else 180.0

        if isinstance(frequency, str):
            frequency = DataFrequency(frequency.lower())

        # Step 2: Create download request
        if progress:
            progress.set_description("Creating download request")
            progress.update(1)

        request = DownloadRequest(
            request_id=request_id,
            variables=variables,
            start_date=start_date,
            end_date=end_date,
            north=north,
            west=west,
            south=south,
            east=east,
            dataset_type=DatasetType.SURFACE,
            frequency=frequency,
            resolution=resolution,
        )

        # Step 3: Execute download
        if progress:
            progress.set_description("Downloading from CDS")
            progress.update(1)

        downloader = ERA5Downloader(**kwargs)
        result = downloader.download(request)
        
        if progress:
            progress.set_description("Download completed")
            progress.close()
        
        return result
        
    except Exception as e:
        if progress:
            progress.close()
        raise


def download_atmospheric_data(
    request_id: str,
    variables: Optional[List[str]] = None,
    start_date: Optional[Union[str, datetime]] = None,
    end_date: Optional[Union[str, datetime]] = None,
    north: Optional[float] = None,
    west: Optional[float] = None,
    south: Optional[float] = None,
    east: Optional[float] = None,
    geometry: Optional[Union[str, Dict]] = None,
    pressure_levels: Optional[List[str]] = None,
    frequency: Union[str, DataFrequency] = DataFrequency.HOURLY,
    resolution: float = DEFAULT_RESOLUTION,
    verbose: bool = False,
    show_progress: bool = True,
    **kwargs,
) -> str:
    """
    Download atmospheric/pressure-level ERA5 data.

    Args:
        request_id: Unique identifier for the request
        variables: List of atmospheric variables (defaults to DEFAULT_ATMOSPHERIC_VARIABLES)
        start_date: Start date for data retrieval (string or datetime)
        end_date: End date for data retrieval (string or datetime)
        north, west, south, east: Bounding box coordinates (optional if geometry provided)
        geometry: Path to GeoJSON file or geometry dict (alternative to bbox)
        pressure_levels: List of pressure levels (defaults to AURORA_PRESSURE_LEVELS)
        frequency: Data frequency
        resolution: Grid resolution in degrees
        verbose: Enable verbose logging
        show_progress: Show progress bar for downloads
        **kwargs: Additional arguments for ERA5Downloader

    Returns:
        Path to the downloaded file
    """
    from ..utils.validation import parse_date, extract_bbox_from_geometry
    from ..utils.io import load_json_file
    from .. import set_verbosity, _is_notebook
    
    # Handle verbosity
    if verbose:
        set_verbosity('INFO')
    
    # Setup progress bar
    in_notebook = _is_notebook()
    if show_progress and in_notebook:
        try:
            from tqdm.notebook import tqdm
            progress = tqdm(total=3, desc="Downloading atmospheric data")
        except ImportError:
            from tqdm import tqdm
            progress = tqdm(total=3, desc="Downloading atmospheric data")
    elif show_progress:
        try:
            from tqdm import tqdm
            progress = tqdm(total=3, desc="Downloading atmospheric data")
        except ImportError:
            progress = None
    else:
        progress = None
    
    try:
        # Step 1: Parse parameters
        if progress:
            progress.set_description("Parsing parameters")
            progress.update(1)
        
        # Set defaults
        variables = variables or DEFAULT_ATMOSPHERIC_VARIABLES
        pressure_levels = pressure_levels or AURORA_PRESSURE_LEVELS
        start_date = parse_date(start_date) if start_date else datetime(2024, 1, 1)
        end_date = parse_date(end_date) if end_date else datetime(2024, 1, 2)

        # Handle geometry vs bounding box
        if geometry:
            if isinstance(geometry, str):
                geometry_data = load_json_file(geometry)
            else:
                geometry_data = geometry
            north, west, south, east = extract_bbox_from_geometry(geometry_data)
        else:
            # Use provided bbox or defaults
            north = north if north is not None else 90.0
            west = west if west is not None else -180.0
            south = south if south is not None else -90.0
            east = east if east is not None else 180.0

        if isinstance(frequency, str):
            frequency = DataFrequency(frequency.lower())

        # Step 2: Create download request
        if progress:
            progress.set_description("Creating download request")
            progress.update(1)

        request = DownloadRequest(
            request_id=request_id,
            variables=variables,
            start_date=start_date,
            end_date=end_date,
            north=north,
            west=west,
            south=south,
            east=east,
            dataset_type=DatasetType.PRESSURE,
            frequency=frequency,
            resolution=resolution,
            pressure_levels=pressure_levels,
        )

        # Step 3: Execute download
        if progress:
            progress.set_description("Downloading from CDS")
            progress.update(1)

        downloader = ERA5Downloader(**kwargs)
        result = downloader.download(request)
        
        if progress:
            progress.set_description("Download completed")
            progress.close()
        
        return result
        
    except Exception as e:
        if progress:
            progress.close()
        raise


def download_static_data(
    request_id: str,
    variables: Optional[List[str]] = None,
    north: Optional[float] = None,
    west: Optional[float] = None,
    south: Optional[float] = None,
    east: Optional[float] = None,
    geometry: Optional[Union[str, Dict]] = None,
    resolution: float = DEFAULT_RESOLUTION,
    verbose: bool = False,
    show_progress: bool = True,
    **kwargs,
) -> str:
    """
    Download static ERA5 variables.

    Args:
        request_id: Unique identifier for the request
        variables: List of static variables (defaults to DEFAULT_STATIC_VARIABLES)
        north, west, south, east: Bounding box coordinates (optional if geometry provided)
        geometry: Path to GeoJSON file or geometry dict (alternative to bbox)
        resolution: Grid resolution in degrees
        verbose: Enable verbose logging
        show_progress: Show progress bar for downloads
        **kwargs: Additional arguments for ERA5Downloader

    Returns:
        Path to the downloaded file
    """
    from ..utils.validation import extract_bbox_from_geometry
    from ..utils.io import load_json_file
    from .. import set_verbosity, _is_notebook
    
    # Handle verbosity
    if verbose:
        set_verbosity('INFO')
    
    # Setup progress bar
    in_notebook = _is_notebook()
    if show_progress and in_notebook:
        try:
            from tqdm.notebook import tqdm
            progress = tqdm(total=3, desc="Downloading static data")
        except ImportError:
            from tqdm import tqdm
            progress = tqdm(total=3, desc="Downloading static data")
    elif show_progress:
        try:
            from tqdm import tqdm
            progress = tqdm(total=3, desc="Downloading static data")
        except ImportError:
            progress = None
    else:
        progress = None
    
    try:
        # Step 1: Parse parameters
        if progress:
            progress.set_description("Parsing parameters")
            progress.update(1)
        
        variables = variables or DEFAULT_STATIC_VARIABLES

        # Handle geometry vs bounding box
        if geometry:
            if isinstance(geometry, str):
                geometry_data = load_json_file(geometry)
            else:
                geometry_data = geometry
            north, west, south, east = extract_bbox_from_geometry(geometry_data)
        else:
            # Use provided bbox or defaults
            north = north if north is not None else 90.0
            west = west if west is not None else -180.0
            south = south if south is not None else -90.0
            east = east if east is not None else 180.0

        # Step 2: Create download request
        if progress:
            progress.set_description("Creating download request")
            progress.update(1)

        request = DownloadRequest(
            request_id=request_id,
            variables=variables,
            start_date=datetime(2023, 1, 1),  # Arbitrary date for static data
            end_date=datetime(2023, 1, 1),
            north=north,
            west=west,
            south=south,
            east=east,
            dataset_type=DatasetType.STATIC,
            frequency=DataFrequency.HOURLY,  # Not used for static data
            resolution=resolution,
        )

        # Step 3: Execute download
        if progress:
            progress.set_description("Downloading from CDS")
            progress.update(1)

        downloader = ERA5Downloader(**kwargs)
        result = downloader.download(request)
        
        if progress:
            progress.set_description("Download completed")
            progress.close()
        
        return result
        
    except Exception as e:
        if progress:
            progress.close()
        raise
