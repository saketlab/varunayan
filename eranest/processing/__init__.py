"""
Data processing module for ERA5 data manipulation.

This module handles all data processing operations including
filtering, aggregation, and format conversion.
"""

from .data import (
    DataProcessor,
    aggregate_temporal_data,
    process_netcdf_dataset,
    process_era5_data,
)

__all__ = [
    "DataProcessor",
    "process_netcdf_dataset",
    "process_era5_data",
    "aggregate_temporal_data",
]
