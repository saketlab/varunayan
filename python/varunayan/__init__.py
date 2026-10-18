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
    heat_index_from_dewpoint,
    heat_index_risk_category,
    humidex,
    mean_radiant_temperature,
    relative_humidity_from_dewpoint,
    utci,
    utci_category,
    utci_sparse,
    vapor_pressure_from_dewpoint,
    wbgt_outdoor,
    wbgt_risk_category,
    wbgt_shade,
    wbgt_simple,
    wet_bulb_from_dewpoint,
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

from .imd_stations import get_imd_stations

from .imd import (
    aggregate_imd_by_frequency,
    download_imd_rainfall,
    download_imd_temperature,
    filter_imd_by_bbox,
    filter_imd_by_geojson,
    get_imd_grid_specs,
    imd_rainfall_bbox,
    imd_rainfall_geojson,
    imd_temperature_bbox,
    imd_temperature_geojson,
    list_imd_datasets,
    process_imd_files,
    read_imd_rainfall,
    read_imd_temperature,
)

from .hadex3 import hadex3_bbox, hadex3_geojson, list_hadex3_indices

from .cru_ts import cru_ts_bbox, cru_ts_geojson, list_cru_ts_variables

from .country import get_era5_country_temperature

ensure_cdsapi_config()

__all__ = [
    "era5ify_geojson",
    "era5ify_bbox",
    "era5ify_point",
    "describe_variables",
    "search_variable",
    "list_available_variables",
    "get_available_pressure_levels",
    "get_variable_info",
    "get_variable_units",
    "get_variable_long_name",
    "list_variable_categories",
    "relative_humidity_from_dewpoint",
    "vapor_pressure_from_dewpoint",
    "wet_bulb_temperature",
    "wet_bulb_from_dewpoint",
    "heat_index",
    "heat_index_from_dewpoint",
    "wbgt_simple",
    "wbgt_shade",
    "wbgt_outdoor",
    "humidex",
    "mean_radiant_temperature",
    "utci",
    "utci_sparse",
    "heat_index_risk_category",
    "wbgt_risk_category",
    "utci_category",
    "calc_heat_indices",
    "get_era5_daily_temperature",
    "get_era5_daily_humidity",
    "get_era5_daily_wind",
    "get_era5_daily_heat_index_data",
    "get_era5_monthly_heat_index_data",
    "get_era5_daily_heat_index_geojson",
    "get_era5_daily_heat_index_point",
    "get_cache_dir",
    "show_cache_info",
    "list_cache",
    "cache_stats",
    "clear_cache",
    "cache_exists",
    "get_cached_data",
    "save_to_cache",
    "invalidate_cache",
    "aggregate_to_polygons",
    "check_grid_coverage",
    "visualize_grid_overlap",
    "compare_grids",
    "get_polygon_timeseries",
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
    "get_imd_stations",
    "get_imd_grid_specs",
    "list_imd_datasets",
    "download_imd_rainfall",
    "download_imd_temperature",
    "read_imd_temperature",
    "read_imd_rainfall",
    "process_imd_files",
    "filter_imd_by_bbox",
    "filter_imd_by_geojson",
    "aggregate_imd_by_frequency",
    "imd_rainfall_bbox",
    "imd_rainfall_geojson",
    "imd_temperature_bbox",
    "imd_temperature_geojson",
    "list_hadex3_indices",
    "hadex3_bbox",
    "hadex3_geojson",
    "list_cru_ts_variables",
    "cru_ts_bbox",
    "cru_ts_geojson",
    "get_era5_country_temperature",
]

__version__ = "0.2.0"
