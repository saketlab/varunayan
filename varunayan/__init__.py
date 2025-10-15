from .config import ensure_cdsapi_config
from .core import era5ify_bbox, era5ify_geojson, era5ify_point
from .search_and_desc import describe_variables, search_variable

ensure_cdsapi_config()

__all__ = [
    "era5ify_geojson",
    "era5ify_bbox",
    "era5ify_point",
    "describe_variables",
    "search_variable",
]

__version__ = "0.1.0"
