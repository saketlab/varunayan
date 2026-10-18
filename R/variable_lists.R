#' ERA5 variable aggregation rules
#'
#' @name variable_lists
#' @noRd
NULL

#' Variables to sum over time
#'
#' Accumulation variables (precipitation, radiation). Temporal aggregation uses
#' the sum for these variables.
#'
#' @return A character vector of variable names.
#' @export
#' @examples
#' head(sum_vars)
sum_vars <- c(
  "tp", "total_precipitation",
  "cp", "convective_precipitation",
  "lsp", "large_scale_precipitation",
  "sf", "snowfall",
  "csf", "convective_snowfall",
  "lsf", "large_scale_snowfall",
  "ssr", "surface_net_solar_radiation",
  "str", "surface_net_thermal_radiation",
  "tsr", "top_net_solar_radiation",
  "ttr", "top_net_thermal_radiation",
  "ssrd", "surface_solar_radiation_downward",
  "strd", "surface_thermal_radiation_downward",
  "tisr", "toa_incident_solar_radiation",
  "slhf", "surface_latent_heat_flux",
  "sshf", "surface_sensible_heat_flux",
  "ewss", "eastward_turbulent_surface_stress",
  "nsss", "northward_turbulent_surface_stress",
  "ro", "runoff",
  "sro", "surface_runoff",
  "ssro", "sub_surface_runoff",
  "e", "evaporation",
  "pev", "potential_evaporation",
  "es", "snow_evaporation",
  "smlt", "snowmelt",
  "bld", "boundary_layer_dissipation",
  "gwd", "gravity_wave_dissipation",
  "cdir", "clear_sky_direct_solar_radiation",
  "uvb", "downward_uv_radiation",
  "lgws", "eastward_gravity_wave_surface_stress",
  "lspf", "large_scale_precipitation_fraction",
  "mgws", "meridional_gravity_wave_surface_stress",
  "ssrc", "surface_net_solar_radiation_clear_sky",
  "strc", "surface_net_thermal_radiation_clear_sky",
  "ssrdc", "surface_solar_radiation_downward_clear_sky",
  "strdc", "surface_thermal_radiation_downward_clear_sky",
  "tsrc", "top_net_solar_radiation_clear_sky",
  "ttrc", "top_net_thermal_radiation_clear_sky",
  "fdir", "total_sky_direct_solar_radiation",
  "vimd", "vertically_integrated_moisture_divergence"
)

#' Variables for maximum aggregation
#'
#' @return A character vector of variable names.
#' @export
#' @examples
#' head(max_vars)
max_vars <- c(
  "mx2t", "maximum_2m_temperature",
  "mxtpr", "maximum_total_precipitation_rate",
  "fg10", "10m_wind_gust",
  "hmax", "maximum_individual_wave_height"
)

#' Variables for minimum aggregation
#'
#' @return A character vector of variable names.
#' @export
#' @examples
#' head(min_vars)
min_vars <- c(
  "mn2t", "minimum_2m_temperature",
  "mntpr", "minimum_total_precipitation_rate"
)

#' Rate variables to average
#'
#' @return A character vector of variable names.
#' @export
#' @examples
#' head(rate_vars)
rate_vars <- c(
  "avg_tprate", "average_total_precipitation_rate",
  "avg_cpr", "average_convective_precipitation_rate",
  "avg_lsprate", "average_large_scale_precipitation_rate",
  "avg_sfrate", "average_snowfall_rate",
  "crr", "convective_rain_rate",
  "lsrr", "large_scale_rain_rate",
  "csfr", "convective_snowfall_rate",
  "lssfr", "large_scale_snowfall_rate",
  "avg_ibld", "average_boundary_layer_dissipation",
  "avg_iegwss", "average_eastward_gravity_wave_surface_stress",
  "avg_iews", "average_eastward_turbulent_surface_stress",
  "avg_ie", "average_evaporation_rate",
  "avg_igwd", "average_gravity_wave_dissipation",
  "avg_ilspf", "average_large_scale_precipitation_fraction",
  "avg_ingwss", "average_northward_gravity_wave_surface_stress",
  "avg_inss", "average_northward_turbulent_surface_stress",
  "avg_pevr", "average_potential_evaporation_rate",
  "avg_rorwe", "average_runoff_rate",
  "avg_esrwe", "average_snow_evaporation_rate",
  "avg_tsrwe", "average_snowfall_rate",
  "avg_smr", "average_snowmelt_rate",
  "avg_ssurfror", "average_sub_surface_runoff_rate",
  "avg_sdirswrf", "average_surface_direct_shortwave_radiation_flux",
  "avg_sdirswrfcs", "average_surface_direct_shortwave_radiation_flux_clear_sky",
  "avg_sdlwrf", "average_surface_downward_long_wave_radiation_flux",
  "avg_sdlwrfcs", "average_surface_downward_long_wave_radiation_flux_clear_sky",
  "avg_sdswrf", "average_surface_downward_shortwave_radiation_flux",
  "avg_sdswrfcs", "average_surface_downward_shortwave_radiation_flux_clear_sky",
  "avg_sduvrf", "average_surface_downward_uv_radiation_flux",
  "avg_slhtf", "average_surface_latent_heat_flux",
  "avg_snlwrf", "average_surface_net_long_wave_radiation_flux",
  "avg_snlwrfcs", "average_surface_net_long_wave_radiation_flux_clear_sky",
  "avg_snswrf", "average_surface_net_shortwave_radiation_flux",
  "avg_snswrfcs", "average_surface_net_shortwave_radiation_flux_clear_sky",
  "avg_surfror", "average_surface_runoff_rate",
  "avg_ishf", "average_surface_sensible_heat_flux",
  "avg_tdswrf", "average_top_downward_shortwave_radiation_flux",
  "avg_tnlwrf", "average_top_net_long_wave_radiation_flux",
  "avg_tnlwrfcs", "average_top_net_long_wave_radiation_flux_clear_sky",
  "avg_tnswrf", "average_top_net_shortwave_radiation_flux",
  "avg_tnswrfcs", "average_top_net_shortwave_radiation_flux_clear_sky",
  "avg_vimdf", "average_vertically_integrated_moisture_divergence"
)

# Non-climate metadata variables that CDS can put in NetCDF files
.NC_METADATA_VARS <- c("number", "expver")

#' Columns to exclude from aggregation
#'
#' Aggregation does not apply to these coordinate and metadata columns.
#'
#' @return A character vector of variable names.
#' @export
#' @examples
#' head(exclude_cols)
exclude_cols <- c(
  "latitude", "longitude", "date", "time", "hour",
  .NC_METADATA_VARS, "valid_time", "datetime", "variable"
)

#' Find if a variable uses sum aggregation
#'
#' @param var_name Variable name as a character string
#' @return Logical. TRUE if the variable uses sum aggregation
#' @export
#' @examples
#' is_sum_var("total_precipitation")
is_sum_var <- function(var_name) {
  var_lower <- tolower(x = var_name)
  any(vapply(sum_vars, function(sv) {
    sv_lower <- tolower(x = sv)
    sv_lower == var_lower || sv_lower %in% strsplit(x = var_lower, split = "_")[[1]]
  }, logical(1)))
}

#' Find if a variable uses maximum aggregation
#'
#' @param var_name Variable name as a character string
#' @return Logical. TRUE if the variable uses maximum aggregation
#' @export
#' @examples
#' is_max_var("2m_temperature")
is_max_var <- function(var_name) {
  var_lower <- tolower(x = var_name)
  any(vapply(max_vars, function(mv) {
    mv_lower <- tolower(x = mv)
    mv_lower == var_lower || mv_lower %in% strsplit(x = var_lower, split = "_")[[1]]
  }, logical(1)))
}

#' Find if a variable uses minimum aggregation
#'
#' @param var_name Variable name as a character string
#' @return Logical. TRUE if the variable uses minimum aggregation
#' @export
#' @examples
#' is_min_var("2m_temperature")
is_min_var <- function(var_name) {
  var_lower <- tolower(x = var_name)
  any(vapply(min_vars, function(mv) {
    mv_lower <- tolower(x = mv)
    mv_lower == var_lower || mv_lower %in% strsplit(x = var_lower, split = "_")[[1]]
  }, logical(1)))
}

#' Find if a variable is a rate variable
#'
#' @param var_name Variable name as a character string
#' @return Logical. TRUE if the variable is a rate
#' @export
#' @examples
#' is_rate_var("2m_temperature")
is_rate_var <- function(var_name) {
  var_lower <- tolower(x = var_name)
  any(vapply(rate_vars, function(rv) {
    rv_lower <- tolower(x = rv)
    rv_lower == var_lower || rv_lower %in% strsplit(x = var_lower, split = "_")[[1]]
  }, logical(1)))
}

#' Sort variables by aggregation method
#'
#' @param var_names Character vector of variable names
#' @return Named list of the variables, sorted by aggregation method
#' @export
#' @examples
#' categorize_variables(c("2m_temperature", "total_precipitation"))
categorize_variables <- function(var_names) {
  # Remove the excluded columns
  var_names <- setdiff(var_names, exclude_cols)

  sum_cols <- var_names[vapply(var_names, is_sum_var, logical(1))]
  max_cols <- var_names[vapply(var_names, is_max_var, logical(1))]
  min_cols <- var_names[vapply(var_names, is_min_var, logical(1))]
  rate_cols <- var_names[vapply(var_names, is_rate_var, logical(1))]

  # Average columns are the columns that the other methods do not include
  special_cols <- unique(x = c(sum_cols, max_cols, min_cols, rate_cols))
  avg_cols <- setdiff(var_names, special_cols)

  list(
    sum = sum_cols,
    max = max_cols,
    min = min_cols,
    rate = rate_cols,
    avg = avg_cols
  )
}

.aggregation_method <- function(var_name) {
  if (is_sum_var(var_name)) "sum" else if (is_max_var(var_name)) "max" else if (is_min_var(var_name)) "min" else "mean"
}
