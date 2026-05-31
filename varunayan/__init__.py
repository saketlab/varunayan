from .config import ensure_cdsapi_config
from .core import era5ify_bbox, era5ify_geojson, era5ify_point

from .search_and_desc import (
    describe_variables,
    get_available_pressure_levels,
    get_variable_info,
    get_variable_long_name,
    get_variable_units,
    list_available_variables,
    list_variable_categories,
    search_variable,
)

from .heat_stress import (
    calc_heat_indices,
    heat_index,
    heat_index_risk_category,
    humidex,
    mean_radiant_temperature,
    relative_humidity_from_dewpoint,
    utci,
    utci_category,
    vapor_pressure_from_dewpoint,
    wbgt_outdoor,
    wbgt_risk_category,
    wbgt_shade,
    wbgt_simple,
    wet_bulb_temperature,
)

from .convenience import (
    get_era5_daily_heat_index_data,
    get_era5_daily_heat_index_geojson,
    get_era5_daily_heat_index_point,
    get_era5_daily_humidity,
    get_era5_daily_temperature,
    get_era5_daily_wind,
    get_era5_monthly_heat_index_data,
)

from .cache import (
    cache_exists,
    cache_stats,
    clear_cache,
    get_cache_dir,
    get_cached_data,
    invalidate_cache,
    list_cache,
    save_to_cache,
    show_cache_info,
)

from .spatial import (
    aggregate_to_polygons,
    check_grid_coverage,
    compare_grids,
    get_polygon_timeseries,
    visualize_grid_overlap,
)

from .processing import (
    categorize_variables,
    get_aggregation_method,
    is_max_var,
    is_min_var,
    is_rate_var,
    is_sum_var,
    max_vars,
    min_vars,
    rate_vars,
    sum_vars,
)

ensure_cdsapi_config()

ensure_cdsapi_config()

__all__ = [
    # Core ERA5 functions
    "era5ify_geojson",
    "era5ify_bbox",
    "era5ify_point",
    # Variable discovery
    "describe_variables",
    "search_variable",
    "list_available_variables",
    "get_available_pressure_levels",
    "get_variable_info",
    "get_variable_units",
    "get_variable_long_name",
    "list_variable_categories",
    # Heat stress indices
    "relative_humidity_from_dewpoint",
    "vapor_pressure_from_dewpoint",
    "wet_bulb_temperature",
    "heat_index",
    "wbgt_simple",
    "wbgt_shade",
    "wbgt_outdoor",
    "humidex",
    "mean_radiant_temperature",
    "utci",
    "heat_index_risk_category",
    "wbgt_risk_category",
    "utci_category",
    "calc_heat_indices",
    # Convenience wrappers
    "get_era5_daily_temperature",
    "get_era5_daily_humidity",
    "get_era5_daily_wind",
    "get_era5_daily_heat_index_data",
    "get_era5_monthly_heat_index_data",
    "get_era5_daily_heat_index_geojson",
    "get_era5_daily_heat_index_point",
    # Caching
    "get_cache_dir",
    "show_cache_info",
    "list_cache",
    "cache_stats",
    "clear_cache",
    "cache_exists",
    "get_cached_data",
    "save_to_cache",
    "invalidate_cache",
    # Spatial aggregation
    "aggregate_to_polygons",
    "check_grid_coverage",
    "visualize_grid_overlap",
    "compare_grids",
    "get_polygon_timeseries",
    # Variable categorization
    "sum_vars",
    "max_vars",
    "min_vars",
    "rate_vars",
    "is_sum_var",
    "is_max_var",
    "is_min_var",
    "is_rate_var",
    "categorize_variables",
    "get_aggregation_method",
]

__version__ = "0.2.0"
