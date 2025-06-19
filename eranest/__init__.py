"""
eranest: Optimized ERA5 Climate Data Processing Package

A high-performance Python package for downloading, processing, and analyzing
ERA5 climate data with support for Microsoft Aurora weather models.

Main Features:
- Efficient ERA5 data downloading from ECMWF CDS
- Optimized spatial and temporal filtering
- Microsoft Aurora model integration
- High-performance data processing with memory optimization
- Comprehensive geospatial operations

Basic Usage:
    >>> import eranest
    >>> 
    >>> # Download surface data
    >>> surface_file = eranest.download_surface_data(
    ...     request_id="my_request",
    ...     start_date=datetime(2024, 1, 1),
    ...     end_date=datetime(2024, 1, 2),
    ...     north=60, south=40, east=30, west=10
    ... )
    >>> 
    >>> # Process for Aurora
    >>> aurora_batch = eranest.create_aurora_batch(
    ...     surface_data=surface_df,
    ...     atmospheric_data=atmos_df
    ... )

For more examples and documentation, visit:
https://github.com/JaggeryArray/eranest
"""

# Package metadata
__version__ = "1.0.0"
__author__ = "JaggeryArray"
__email__ = "contact@jaggeryarray.com"
__license__ = "MIT"
__description__ = "Optimized ERA5 climate data processing with Aurora support"

# Core functionality - Main API
from .download import (
    download_surface_data,
    download_atmospheric_data,
    download_static_data,
    ERA5Downloader,
)

from .processing import (
    process_netcdf_dataset,
    aggregate_temporal_data,
    DataProcessor,
)

from .spatial import (
    filter_by_geometry,
    extract_bounding_box,
    validate_coordinates,
    SpatialFilter,
)

from .aurora import (
    era5_to_aurora_format,
    create_aurora_batch,
    AuroraConverter,
)

from .utils import (
    load_json_file,
    save_json_file,
    validate_date_range,
    validate_geojson,
)

# Legacy API for backward compatibility
from .core import era5ify_geojson, era5ify_bbox

# Constants and configurations
from .constants import (
    AURORA_PRESSURE_LEVELS,
    DEFAULT_SURFACE_VARIABLES,
    DEFAULT_ATMOSPHERIC_VARIABLES,
    DEFAULT_STATIC_VARIABLES,
    DataFrequency,
    DatasetType,
)

# Exceptions
from .exceptions import (
    EranestError,
    DataDownloadError,
    DataProcessingError,
    ValidationError,
    GeospatialError,
    AuroraError,
)

# Define public API
__all__ = [
    # Core download functions
    "download_surface_data",
    "download_atmospheric_data", 
    "download_static_data",
    "ERA5Downloader",
    
    # Data processing
    "process_netcdf_dataset",
    "aggregate_temporal_data",
    "DataProcessor",
    
    # Spatial operations
    "filter_by_geometry",
    "extract_bounding_box",
    "validate_coordinates",
    "SpatialFilter",
    
    # Aurora integration
    "era5_to_aurora_format",
    "create_aurora_batch", 
    "AuroraConverter",
    
    # Utilities
    "load_json_file",
    "save_json_file",
    "validate_date_range",
    "validate_geojson",
    
    # Legacy functions
    "era5ify_geojson",
    "era5ify_bbox",
    
    # Constants
    "AURORA_PRESSURE_LEVELS",
    "DEFAULT_SURFACE_VARIABLES",
    "DEFAULT_ATMOSPHERIC_VARIABLES", 
    "DEFAULT_STATIC_VARIABLES",
    "DataFrequency",
    "DatasetType",
    
    # Exceptions
    "EranestError",
    "DataDownloadError",
    "DataProcessingError",
    "ValidationError",
    "GeospatialError",
    "AuroraError",
]

# Configure logging
import logging

# Create package logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler if none exists
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)

# Package initialization
logger.info(f"eranest v{__version__} initialized")

# Performance monitoring setup
import sys
import warnings

def _check_optional_dependencies():
    """Check for optional dependencies and warn if missing."""
    optional_deps = {
        'torch': 'PyTorch (for Aurora integration)',
        'dask': 'Dask (for parallel processing)',
        'cartopy': 'Cartopy (for advanced plotting)',
    }
    
    missing_deps = []
    for dep, description in optional_deps.items():
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(f"{dep} ({description})")
    
    if missing_deps:
        logger.info(f"Optional dependencies not available: {', '.join(missing_deps)}")
        logger.info("Install with: pip install eranest[full] for all features")

# Check dependencies on import
_check_optional_dependencies()

# Set up memory monitoring
def _setup_memory_monitoring():
    """Set up memory usage monitoring."""
    try:
        import psutil
        
        # Check available memory
        memory = psutil.virtual_memory()
        if memory.available < 2 * 1024**3:  # Less than 2GB
            warnings.warn(
                "Low memory detected. Consider using chunked processing for large datasets.",
                ResourceWarning
            )
        
        logger.debug(f"System memory: {memory.total / 1024**3:.1f} GB total, "
                    f"{memory.available / 1024**3:.1f} GB available")
        
    except ImportError:
        logger.debug("psutil not available - memory monitoring disabled")

_setup_memory_monitoring()

# Performance tips
def _show_performance_tips():
    """Show performance optimization tips."""
    if sys.platform.startswith('win'):
        logger.debug("Windows detected - consider using WSL for better performance")
    
    # Check if running in Jupyter
    try:
        get_ipython()  # type: ignore
        logger.debug("Jupyter environment detected - memory optimization enabled")
    except NameError:
        pass  # Not in Jupyter

_show_performance_tips()

# Clean up namespace
del logging, sys, warnings, _check_optional_dependencies, _setup_memory_monitoring, _show_performance_tips