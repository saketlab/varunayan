"""
Optimized data processing operations for ERA5 datasets.

This module provides high-performance data processing capabilities
with memory-efficient algorithms and vectorized operations.
"""

import logging
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr

# Try to import dask, but make it optional
try:
    import dask

    DASK_AVAILABLE = True
    # Suppress dask warnings for cleaner output
    try:
        warnings.filterwarnings("ignore", module="dask")
    except Exception:
        pass  # Ignore warning filter errors
except ImportError:
    DASK_AVAILABLE = False
    dask = None

from ..constants import (
    AURORA_PRESSURE_LEVELS,
    DEFAULT_CHUNK_SIZE,
    MAX_MEMORY_USAGE_MB,
    DataFrequency,
)
from ..exceptions import DataProcessingError
from ..exceptions import MemoryError as EranestMemoryError
from ..spatial.filtering import FilterResult, SpatialFilter
from ..utils.io import load_netcdf_dataset
from ..utils.validation import validate_dataframe_structure, validate_date_range

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of data processing operation."""

    processed_data: pd.DataFrame
    processing_time: float
    memory_usage_mb: float
    records_processed: int
    records_filtered: int
    metadata: Dict[str, Any]


class DataProcessor:
    """
    High-performance data processor with memory optimization and parallel processing.

    This class provides efficient processing of large ERA5 datasets with
    automatic memory management and performance monitoring.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_memory_mb: int = MAX_MEMORY_USAGE_MB,
        parallel_processing: bool = True,
        max_workers: int = 4,
        use_dask: bool = True,
    ):
        """
        Initialize the data processor.

        Args:
            chunk_size: Size of data chunks for processing
            max_memory_mb: Maximum memory usage in MB
            parallel_processing: Enable parallel processing
            max_workers: Maximum number of parallel workers
            use_dask: Use Dask for lazy evaluation and parallel computing
        """
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers
        self.use_dask = use_dask

        self._processing_stats = {
            "total_processed": 0,
            "total_time": 0.0,
            "peak_memory": 0.0,
        }

        # Configure Dask if enabled and available
        if self.use_dask and DASK_AVAILABLE:
            self._configure_dask()
        elif self.use_dask and not DASK_AVAILABLE:
            logger.warning("Dask not available, falling back to pandas processing")
            self.use_dask = False

    def _configure_dask(self) -> None:
        """Configure Dask for optimal performance."""
        if not DASK_AVAILABLE:
            logger.warning("Dask not available, falling back to pandas processing")
            self.use_dask = False
            return

        try:
            # Set up Dask configuration
            dask.config.set(
                {
                    "array.chunk-size": f"{self.chunk_size}MiB",
                    "distributed.worker.memory.target": 0.8,
                    "distributed.worker.memory.spill": 0.9,
                    "distributed.worker.memory.pause": 0.95,
                }
            )

            logger.debug("Dask configured for optimized processing")
        except Exception as e:
            logger.warning(
                f"Dask configuration failed: {e}, falling back to pandas processing"
            )
            self.use_dask = False

    def process_netcdf_files(
        self,
        file_paths: List[str],
        geometry: Optional[Dict[str, Any]] = None,
        variables: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> ProcessingResult:
        """
        Process multiple NetCDF files efficiently.

        Args:
            file_paths: List of NetCDF file paths
            geometry: Optional geometry for spatial filtering
            variables: List of variables to extract
            time_range: Optional time range for temporal filtering

        Returns:
            ProcessingResult with combined processed data
        """
        import time

        import psutil

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        logger.info(f"Processing {len(file_paths)} NetCDF files...")

        processed_datasets = []
        total_records = 0

        if self.parallel_processing and len(file_paths) > 1:
            # Parallel processing
            processed_datasets = self._process_files_parallel(
                file_paths, geometry, variables, time_range
            )
        else:
            # Sequential processing
            for file_path in file_paths:
                result = self._process_single_file(
                    file_path, geometry, variables, time_range
                )
                if result is not None:
                    processed_datasets.append(result)
                    total_records += len(result)

        # Combine all datasets
        if processed_datasets:
            combined_data = self._combine_datasets(processed_datasets)
        else:
            combined_data = pd.DataFrame()

        # Calculate metrics
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        processing_time = end_time - start_time
        memory_usage = end_memory - start_memory

        # Update stats
        self._processing_stats["total_processed"] += len(combined_data)
        self._processing_stats["total_time"] += processing_time
        self._processing_stats["peak_memory"] = max(
            self._processing_stats["peak_memory"], memory_usage
        )

        result = ProcessingResult(
            processed_data=combined_data,
            processing_time=processing_time,
            memory_usage_mb=memory_usage,
            records_processed=total_records,
            records_filtered=len(combined_data),
            metadata={
                "files_processed": len(file_paths),
                "variables": variables,
                "spatial_filtered": geometry is not None,
                "temporal_filtered": time_range is not None,
            },
        )

        logger.info(f"Processing completed in {processing_time:.2f}s")
        logger.info(f"Memory usage: {memory_usage:.1f} MB")
        logger.info(f"Records: {total_records} → {len(combined_data)} (filtered)")

        return result

    def _process_files_parallel(
        self,
        file_paths: List[str],
        geometry: Optional[Dict[str, Any]],
        variables: Optional[List[str]],
        time_range: Optional[Tuple[datetime, datetime]],
    ) -> List[pd.DataFrame]:
        """Process files in parallel."""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all processing tasks
            future_to_file = {
                executor.submit(
                    self._process_single_file,
                    file_path,
                    geometry,
                    variables,
                    time_range,
                ): file_path
                for file_path in file_paths
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                        logger.debug(f"Processed {file_path}: {len(result)} records")
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

        return results

    def _process_single_file(
        self,
        file_path: str,
        geometry: Optional[Dict[str, Any]],
        variables: Optional[List[str]],
        time_range: Optional[Tuple[datetime, datetime]],
    ) -> Optional[pd.DataFrame]:
        """Process a single NetCDF file."""
        try:
            # Load dataset
            dataset = load_netcdf_dataset(file_path)

            # Filter variables if specified
            if variables:
                available_vars = list(dataset.data_vars)
                selected_vars = [var for var in variables if var in available_vars]
                if selected_vars:
                    dataset = dataset[selected_vars]
                else:
                    logger.warning(f"No requested variables found in {file_path}")
                    return None

            # Apply temporal filtering
            if time_range:
                dataset = self._filter_temporal(dataset, time_range)
                if dataset.time.size == 0:
                    logger.debug(f"No data in time range for {file_path}")
                    return None

            # Apply spatial filtering
            if geometry:
                spatial_filter = SpatialFilter(
                    chunk_size=self.chunk_size,
                    parallel_processing=False,  # Already parallel at file level
                )
                filter_result = spatial_filter.filter_dataset(dataset, geometry)
                df = filter_result.filtered_data
            else:
                df = dataset.to_dataframe().reset_index()

            return df

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None

    def _filter_temporal(
        self, dataset: xr.Dataset, time_range: Tuple[datetime, datetime]
    ) -> xr.Dataset:
        """Apply temporal filtering to dataset."""
        start_date, end_date = time_range

        # Validate time range
        validate_date_range(start_date, end_date)

        # Convert to pandas datetime for comparison
        time_coord = dataset.time

        # Apply time filter
        mask = (time_coord >= start_date) & (time_coord <= end_date)
        filtered_dataset = dataset.sel(time=mask)

        logger.debug(
            f"Temporal filter: {time_coord.size} → {filtered_dataset.time.size} time steps"
        )

        return filtered_dataset

    def _combine_datasets(self, datasets: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine multiple datasets efficiently."""
        if not datasets:
            return pd.DataFrame()

        if len(datasets) == 1:
            return datasets[0]

        # Check memory usage before combining
        total_memory_mb = (
            sum(df.memory_usage(deep=True).sum() for df in datasets) / 1024 / 1024
        )

        if total_memory_mb > self.max_memory_mb:
            logger.warning(f"Large memory usage detected: {total_memory_mb:.1f} MB")
            # Process in chunks to avoid memory issues
            return self._combine_datasets_chunked(datasets)

        # Standard concatenation
        combined = pd.concat(datasets, ignore_index=True)

        # Remove duplicates if any
        if (
            "time" in combined.columns
            and "latitude" in combined.columns
            and "longitude" in combined.columns
        ):
            initial_len = len(combined)
            combined = combined.drop_duplicates(
                subset=["time", "latitude", "longitude"]
            )
            if len(combined) < initial_len:
                logger.info(f"Removed {initial_len - len(combined)} duplicate records")

        return combined

    def _combine_datasets_chunked(self, datasets: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine datasets in chunks to manage memory."""
        logger.info("Using chunked combination to manage memory")

        # Sort datasets by size (smallest first)
        datasets.sort(key=len)

        result = datasets[0]

        for i, df in enumerate(datasets[1:], 1):
            # Check memory before adding next dataset
            current_memory = result.memory_usage(deep=True).sum() / 1024 / 1024
            next_memory = df.memory_usage(deep=True).sum() / 1024 / 1024

            if current_memory + next_memory > self.max_memory_mb:
                # Process current result to reduce memory
                result = self._optimize_dataframe_memory(result)

            result = pd.concat([result, df], ignore_index=True)

            logger.debug(
                f"Combined dataset {i+1}/{len(datasets)}: {len(result)} records"
            )

        return result

    def _optimize_dataframe_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        initial_memory = df.memory_usage(deep=True).sum() / 1024 / 1024

        # Optimize numeric columns
        for col in df.select_dtypes(include=["int64"]).columns:
            if df[col].min() >= 0:
                if df[col].max() < 255:
                    df[col] = df[col].astype("uint8")
                elif df[col].max() < 65535:
                    df[col] = df[col].astype("uint16")
                elif df[col].max() < 4294967295:
                    df[col] = df[col].astype("uint32")
            else:
                if df[col].min() > -128 and df[col].max() < 127:
                    df[col] = df[col].astype("int8")
                elif df[col].min() > -32768 and df[col].max() < 32767:
                    df[col] = df[col].astype("int16")
                elif df[col].min() > -2147483648 and df[col].max() < 2147483647:
                    df[col] = df[col].astype("int32")

        # Optimize float columns
        for col in df.select_dtypes(include=["float64"]).columns:
            df[col] = pd.to_numeric(df[col], downcast="float")

        # Optimize object columns
        for col in df.select_dtypes(include=["object"]).columns:
            if df[col].nunique() / len(df) < 0.5:  # Many repeated values
                df[col] = df[col].astype("category")

        final_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        saved_memory = initial_memory - final_memory

        logger.debug(
            f"Memory optimization: {initial_memory:.1f} → {final_memory:.1f} MB "
            f"(saved {saved_memory:.1f} MB)"
        )

        return df

    def aggregate_temporal_data(
        self,
        df: pd.DataFrame,
        frequency: Union[str, DataFrequency],
        aggregation_method: str = "mean",
        time_column: str = "time",
    ) -> pd.DataFrame:
        """
        Aggregate data temporally with specified frequency.

        Args:
            df: DataFrame to aggregate
            frequency: Aggregation frequency
            aggregation_method: Aggregation method (mean, sum, min, max, std)
            time_column: Name of time column

        Returns:
            Temporally aggregated DataFrame
        """
        if time_column not in df.columns:
            raise DataProcessingError(
                f"Time column '{time_column}' not found in DataFrame"
            )

        # Convert frequency to pandas frequency string
        if isinstance(frequency, DataFrequency):
            freq_str = {
                DataFrequency.HOURLY: "H",
                DataFrequency.DAILY: "D",
                DataFrequency.WEEKLY: "W",
                DataFrequency.MONTHLY: "M",
                DataFrequency.YEARLY: "Y",
            }[frequency]
        else:
            freq_mapping = {
                "hourly": "H",
                "daily": "D",
                "weekly": "W",
                "monthly": "M",
                "yearly": "Y",
            }
            freq_str = freq_mapping.get(frequency.lower(), frequency)

        # Ensure time column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            df[time_column] = pd.to_datetime(df[time_column])

        # Set time as index for resampling
        df_copy = df.set_index(time_column)

        # Identify grouping columns (non-numeric, non-time columns)
        numeric_columns = df_copy.select_dtypes(include=[np.number]).columns
        grouping_columns = [
            col
            for col in df_copy.columns
            if col not in numeric_columns and col != time_column
        ]

        # Perform aggregation
        if grouping_columns:
            # Group by spatial coordinates and aggregate temporally
            grouped = df_copy.groupby(grouping_columns)

            if aggregation_method == "mean":
                aggregated = grouped.resample(freq_str).mean()
            elif aggregation_method == "sum":
                aggregated = grouped.resample(freq_str).sum()
            elif aggregation_method == "min":
                aggregated = grouped.resample(freq_str).min()
            elif aggregation_method == "max":
                aggregated = grouped.resample(freq_str).max()
            elif aggregation_method == "std":
                aggregated = grouped.resample(freq_str).std()
            else:
                raise DataProcessingError(
                    f"Unsupported aggregation method: {aggregation_method}"
                )
        else:
            # Simple temporal aggregation without grouping
            if aggregation_method == "mean":
                aggregated = df_copy.resample(freq_str).mean()
            elif aggregation_method == "sum":
                aggregated = df_copy.resample(freq_str).sum()
            elif aggregation_method == "min":
                aggregated = df_copy.resample(freq_str).min()
            elif aggregation_method == "max":
                aggregated = df_copy.resample(freq_str).max()
            elif aggregation_method == "std":
                aggregated = df_copy.resample(freq_str).std()
            else:
                raise DataProcessingError(
                    f"Unsupported aggregation method: {aggregation_method}"
                )

        # Reset index and clean up
        result = aggregated.reset_index().dropna()

        logger.info(
            f"Temporal aggregation ({frequency}, {aggregation_method}): "
            f"{len(df)} → {len(result)} records"
        )

        return result

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self._processing_stats.copy()

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._processing_stats = {
            "total_processed": 0,
            "total_time": 0.0,
            "peak_memory": 0.0,
        }


# Convenience functions


def process_era5_data(
    file_paths: Union[str, List[str]],
    geometry: Optional[Union[str, Dict[str, Any]]] = None,
    variables: Optional[List[str]] = None,
    time_range: Optional[Tuple[datetime, datetime]] = None,
    auto_rename_variables: bool = True,
    verbose: bool = False,
    show_progress: bool = True,
    **kwargs,
) -> ProcessingResult:
    """
    Process ERA5 NetCDF data with automatic variable name handling.
    
    Args:
        file_paths: Path(s) to NetCDF files
        geometry: Optional geometry for spatial filtering (path to GeoJSON or dict)
        variables: List of variables to extract (uses long or short names automatically)
        time_range: Optional time range for temporal filtering
        auto_rename_variables: Automatically rename variables to long descriptive names
        verbose: Enable verbose logging
        show_progress: Show progress bar for processing
        **kwargs: Additional arguments for DataProcessor
    
    Returns:
        ProcessingResult with processed data and standardized column names
    """
    from ..constants import LEGACY_VARIABLE_MAPPING
    from ..utils.io import load_json_file
    from .. import set_verbosity, _is_notebook
    import xarray as xr
    import pandas as pd
    import time
    import psutil
    
    # Handle verbosity
    if verbose:
        set_verbosity('INFO')
    
    # Setup progress bar
    in_notebook = _is_notebook()
    if show_progress and in_notebook:
        try:
            from tqdm.notebook import tqdm
        except ImportError:
            from tqdm import tqdm
    elif show_progress:
        try:
            from tqdm import tqdm
        except ImportError:
            tqdm = None
    else:
        tqdm = None
    
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    # Handle geometry
    if isinstance(geometry, str):
        geometry = load_json_file(geometry)
    
    # Setup progress bar
    progress = None
    if tqdm:
        total_steps = len(file_paths) + 1  # Files + final combination
        progress = tqdm(total=total_steps, desc="Processing ERA5 data")
    
    all_dataframes = []
    
    try:
        for i, file_path in enumerate(file_paths):
            if progress:
                progress.set_description(f"Processing file {i+1}/{len(file_paths)}")
            
            # Load dataset
            ds = xr.open_dataset(file_path)
            
            # Convert to DataFrame
            df = ds.to_dataframe().reset_index()
            
            # Clean up coordinate names
            if 'valid_time' in df.columns:
                df = df.rename(columns={'valid_time': 'time'})
            if 'pressure_level' in df.columns:
                df = df.rename(columns={'pressure_level': 'level'})
            
            # Drop unnecessary columns
            drop_cols = ['number', 'expver']
            df = df.drop(columns=[col for col in drop_cols if col in df.columns])
            
            # Auto-rename variables if requested
            if auto_rename_variables:
                # ERA5 short to long name mapping
                era5_mappings = {
                    't2m': '2m_temperature',
                    'u10': '10m_u_component_of_wind', 
                    'v10': '10m_v_component_of_wind',
                    'msl': 'mean_sea_level_pressure',
                    't': 'temperature',
                    'u': 'u_component_of_wind',
                    'v': 'v_component_of_wind', 
                    'q': 'specific_humidity',
                    'z': 'geopotential',
                    'lsm': 'land_sea_mask',
                    'slt': 'soil_type'
                }
                df = df.rename(columns=era5_mappings)
            
            # Filter variables if specified
            if variables:
                # Find columns that match requested variables (either short or long names)
                available_cols = set(df.columns)
                coord_cols = {'time', 'latitude', 'longitude', 'level'}
                
                # Keep coordinate columns
                cols_to_keep = list(coord_cols.intersection(available_cols))
                
                # Add requested variables
                for var in variables:
                    if var in available_cols:
                        cols_to_keep.append(var)
                    # Try short name if long name not found
                    elif var in LEGACY_VARIABLE_MAPPING.values():
                        short_name = [k for k, v in LEGACY_VARIABLE_MAPPING.items() if v == var]
                        if short_name and short_name[0] in available_cols:
                            cols_to_keep.append(short_name[0])
                
                df = df[cols_to_keep]
            
            # Apply spatial filtering if geometry provided
            if geometry:
                from ..spatial.filtering import SpatialFilter
                spatial_filter = SpatialFilter()
                
                # Convert DataFrame back to Dataset for spatial filtering
                temp_ds = df.set_index(['time', 'latitude', 'longitude']).to_xarray()
                filter_result = spatial_filter.filter_dataset(temp_ds, geometry)
                df = filter_result.filtered_data
            
            all_dataframes.append(df)
            ds.close()
            
            if progress:
                progress.update(1)
    
        # Combine all DataFrames
        if progress:
            progress.set_description("Combining datasets")
        
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
        else:
            combined_df = pd.DataFrame()
        
        if progress:
            progress.update(1)
            progress.set_description("Processing completed")
            progress.close()
        
        # Calculate metrics
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        processing_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        return ProcessingResult(
            processed_data=combined_df,
            processing_time=processing_time,
            memory_usage_mb=memory_usage,
            records_processed=len(combined_df),
            records_filtered=len(combined_df),
            metadata={
                "files_processed": len(file_paths),
                "variables": variables,
                "spatial_filtered": geometry is not None,
                "temporal_filtered": time_range is not None,
                "auto_renamed": auto_rename_variables,
            },
        )
    
    except Exception as e:
        if progress:
            progress.close()
        raise


def process_netcdf_dataset(
    file_paths: Union[str, List[str]],
    geometry: Optional[Dict[str, Any]] = None,
    variables: Optional[List[str]] = None,
    time_range: Optional[Tuple[datetime, datetime]] = None,
    **kwargs,
) -> ProcessingResult:
    """
    Process NetCDF dataset(s) with optimizations.

    Args:
        file_paths: Path(s) to NetCDF files
        geometry: Optional geometry for spatial filtering
        variables: List of variables to extract
        time_range: Optional time range for temporal filtering
        **kwargs: Additional arguments for DataProcessor

    Returns:
        ProcessingResult with processed data
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    processor = DataProcessor(**kwargs)
    return processor.process_netcdf_files(file_paths, geometry, variables, time_range)


def aggregate_temporal_data(
    df: pd.DataFrame,
    frequency: Union[str, DataFrequency],
    method: str = "mean",
    **kwargs,
) -> pd.DataFrame:
    """
    Aggregate DataFrame temporally.

    Args:
        df: DataFrame to aggregate
        frequency: Aggregation frequency
        method: Aggregation method
        **kwargs: Additional arguments for DataProcessor

    Returns:
        Aggregated DataFrame
    """
    processor = DataProcessor(**kwargs)
    return processor.aggregate_temporal_data(df, frequency, method)
