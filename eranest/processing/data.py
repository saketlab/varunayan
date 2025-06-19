"""
Optimized data processing operations for ERA5 datasets.

This module provides high-performance data processing capabilities
with memory-efficient algorithms and vectorized operations.
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta
import dask
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

from ..constants import (
    DEFAULT_CHUNK_SIZE,
    MAX_MEMORY_USAGE_MB,
    DataFrequency,
    AURORA_PRESSURE_LEVELS,
)
from ..exceptions import DataProcessingError, MemoryError as EranestMemoryError
from ..spatial.filtering import SpatialFilter, FilterResult
from ..utils.validation import validate_dataframe_structure, validate_date_range
from ..utils.io import load_netcdf_dataset

logger = logging.getLogger(__name__)

# Suppress dask warnings for cleaner output
warnings.filterwarnings("ignore", category=dask.config.ConfigWarning)


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
    
    def __init__(self,
                 chunk_size: int = DEFAULT_CHUNK_SIZE,
                 max_memory_mb: int = MAX_MEMORY_USAGE_MB,
                 parallel_processing: bool = True,
                 max_workers: int = 4,
                 use_dask: bool = True):
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
        
        # Configure Dask if enabled
        if self.use_dask:
            self._configure_dask()
    
    def _configure_dask(self) -> None:
        """Configure Dask for optimal performance."""
        try:
            import dask
            from dask.distributed import Client
            
            # Set up Dask configuration
            dask.config.set({
                'array.chunk-size': f"{self.chunk_size}MiB",
                'distributed.worker.memory.target': 0.8,
                'distributed.worker.memory.spill': 0.9,
                'distributed.worker.memory.pause': 0.95,
            })
            
            logger.debug("Dask configured for optimized processing")
        except ImportError:
            logger.warning("Dask not available, falling back to pandas processing")
            self.use_dask = False
    
    def process_netcdf_files(self,
                           file_paths: List[str],
                           geometry: Optional[Dict[str, Any]] = None,
                           variables: Optional[List[str]] = None,
                           time_range: Optional[Tuple[datetime, datetime]] = None) -> ProcessingResult:
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
            }
        )
        
        logger.info(f"Processing completed in {processing_time:.2f}s")
        logger.info(f"Memory usage: {memory_usage:.1f} MB")
        logger.info(f"Records: {total_records} → {len(combined_data)} (filtered)")
        
        return result
    
    def _process_files_parallel(self,
                               file_paths: List[str],
                               geometry: Optional[Dict[str, Any]],
                               variables: Optional[List[str]],
                               time_range: Optional[Tuple[datetime, datetime]]) -> List[pd.DataFrame]:
        """Process files in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all processing tasks
            future_to_file = {
                executor.submit(
                    self._process_single_file,
                    file_path, geometry, variables, time_range
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
    
    def _process_single_file(self,
                           file_path: str,
                           geometry: Optional[Dict[str, Any]],
                           variables: Optional[List[str]],
                           time_range: Optional[Tuple[datetime, datetime]]) -> Optional[pd.DataFrame]:
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
                    parallel_processing=False  # Already parallel at file level
                )
                filter_result = spatial_filter.filter_dataset(dataset, geometry)
                df = filter_result.filtered_data
            else:
                df = dataset.to_dataframe().reset_index()
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None
    
    def _filter_temporal(self,
                        dataset: xr.Dataset,
                        time_range: Tuple[datetime, datetime]) -> xr.Dataset:
        """Apply temporal filtering to dataset."""
        start_date, end_date = time_range
        
        # Validate time range
        validate_date_range(start_date, end_date)
        
        # Convert to pandas datetime for comparison
        time_coord = dataset.time
        
        # Apply time filter
        mask = (time_coord >= start_date) & (time_coord <= end_date)
        filtered_dataset = dataset.sel(time=mask)
        
        logger.debug(f"Temporal filter: {time_coord.size} → {filtered_dataset.time.size} time steps")
        
        return filtered_dataset
    
    def _combine_datasets(self, datasets: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine multiple datasets efficiently."""
        if not datasets:
            return pd.DataFrame()
        
        if len(datasets) == 1:
            return datasets[0]
        
        # Check memory usage before combining
        total_memory_mb = sum(df.memory_usage(deep=True).sum() for df in datasets) / 1024 / 1024
        
        if total_memory_mb > self.max_memory_mb:
            logger.warning(f"Large memory usage detected: {total_memory_mb:.1f} MB")
            # Process in chunks to avoid memory issues
            return self._combine_datasets_chunked(datasets)
        
        # Standard concatenation
        combined = pd.concat(datasets, ignore_index=True)
        
        # Remove duplicates if any
        if 'time' in combined.columns and 'latitude' in combined.columns and 'longitude' in combined.columns:
            initial_len = len(combined)
            combined = combined.drop_duplicates(subset=['time', 'latitude', 'longitude'])
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
            
            logger.debug(f"Combined dataset {i+1}/{len(datasets)}: {len(result)} records")
        
        return result
    
    def _optimize_dataframe_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        initial_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Optimize numeric columns
        for col in df.select_dtypes(include=['int64']).columns:
            if df[col].min() >= 0:
                if df[col].max() < 255:
                    df[col] = df[col].astype('uint8')
                elif df[col].max() < 65535:
                    df[col] = df[col].astype('uint16')
                elif df[col].max() < 4294967295:
                    df[col] = df[col].astype('uint32')
            else:
                if df[col].min() > -128 and df[col].max() < 127:
                    df[col] = df[col].astype('int8')
                elif df[col].min() > -32768 and df[col].max() < 32767:
                    df[col] = df[col].astype('int16')
                elif df[col].min() > -2147483648 and df[col].max() < 2147483647:
                    df[col] = df[col].astype('int32')
        
        # Optimize float columns
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Optimize object columns
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Many repeated values
                df[col] = df[col].astype('category')
        
        final_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        saved_memory = initial_memory - final_memory
        
        logger.debug(f"Memory optimization: {initial_memory:.1f} → {final_memory:.1f} MB "
                    f"(saved {saved_memory:.1f} MB)")
        
        return df
    
    def aggregate_temporal_data(self,
                              df: pd.DataFrame,
                              frequency: Union[str, DataFrequency],
                              aggregation_method: str = "mean",
                              time_column: str = "time") -> pd.DataFrame:
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
            raise DataProcessingError(f"Time column '{time_column}' not found in DataFrame")
        
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
        grouping_columns = [col for col in df_copy.columns 
                          if col not in numeric_columns and col != time_column]
        
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
                raise DataProcessingError(f"Unsupported aggregation method: {aggregation_method}")
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
                raise DataProcessingError(f"Unsupported aggregation method: {aggregation_method}")
        
        # Reset index and clean up
        result = aggregated.reset_index().dropna()
        
        logger.info(f"Temporal aggregation ({frequency}, {aggregation_method}): "
                   f"{len(df)} → {len(result)} records")
        
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

def process_netcdf_dataset(
    file_paths: Union[str, List[str]],
    geometry: Optional[Dict[str, Any]] = None,
    variables: Optional[List[str]] = None,
    time_range: Optional[Tuple[datetime, datetime]] = None,
    **kwargs
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
    **kwargs
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