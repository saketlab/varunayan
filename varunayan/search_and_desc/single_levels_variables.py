temperature_and_pressure = [
    {
        "name": "2m_dewpoint_temperature",
        "description": (
            "Dew point temperature at 2 meters above the surface, "
            "representing "
            "the temperature at which air becomes saturated with moisture. "
            "Unit: Kelvin (K)."
        ),
    },
    {
        "name": "2m_temperature",
        "description": (
            "Air temperature at 2 meters above the surface, typically used to "
            "represent surface-level weather conditions. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "ice_temperature_layer_1",
        "description": (
            "Temperature of the top layer of sea ice. This layer is most "
            "affected by atmospheric conditions. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "ice_temperature_layer_2",
        "description": (
            "Temperature of the second layer of sea ice, representing deeper "
            "internal ice temperatures. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "ice_temperature_layer_3",
        "description": (
            "Temperature of the third layer of sea ice, indicating mid-level "
            "internal ice temperature. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "ice_temperature_layer_4",
        "description": (
            "Temperature of the deepest (fourth) layer of sea ice, typically "
            "least affected by surface variations. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "maximum_2m_temperature_since_previous_post_processing",
        "description": (
            "Maximum 2-meter air temperature recorded since the last "
            "post-processing cycle. Often used to estimate daily high "
            "temperature. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "mean_sea_level_pressure",
        "description": (
            "Atmospheric pressure reduced to sea level, assuming a standard "
            "atmosphere. Useful for weather maps and synoptic analysis. "
            "Unit: Pascal (Pa)."
        ),
    },
    {
        "name": "minimum_2m_temperature_since_previous_post_processing",
        "description": (
            "Minimum 2-meter air temperature recorded since the last "
            "post-processing cycle. Often used to estimate daily low "
            "temperature. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "sea_surface_temperature",
        "description": (
            "Temperature of the ocean surface, typically the upper few "
            "millimeters. Important for weather forecasting and climate "
            "models. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "skin_temperature",
        "description": (
            "Temperature of the Earth's surface (land or sea) as perceived "
            "by a "
            "satellite sensor, also known as surface skin temperature. "
            "Unit: Kelvin (K)."
        ),
    },
    {
        "name": "surface_pressure",
        "description": (
            "Atmospheric pressure at the surface of the Earth. Influenced by "
            "elevation and weather systems. Unit: Pascal (Pa)."
        ),
    },
]

wind_variables = [
    {
        "name": "100m_u_component_of_wind",
        "description": (
            "Zonal (west-east) component of wind at 100 meters "
            "above ground. Positive values indicate wind from west "
            "to east. Unit: m/s."
        ),
    },
    {
        "name": "100m_v_component_of_wind",
        "description": (
            "Meridional (south-north) component of wind at 100 "
            "meters above ground. Positive values indicate wind "
            "from south to north. Unit: m/s."
        ),
    },
    {
        "name": "10m_u_component_of_neutral_wind",
        "description": (
            "Zonal component of neutral stability wind at 10 "
            "meters, assuming no heat exchange with the surface. "
            "Unit: m/s."
        ),
    },
    {
        "name": "10m_u_component_of_wind",
        "description": (
            "Zonal (west-east) component of wind at 10 meters above "
            "surface. Positive values indicate wind from west to "
            "east. Unit: m/s."
        ),
    },
    {
        "name": "10m_v_component_of_neutral_wind",
        "description": (
            "Meridional component of neutral stability wind at 10 "
            "meters, assuming no heat exchange with the surface. "
            "Unit: m/s."
        ),
    },
    {
        "name": "10m_v_component_of_wind",
        "description": (
            "Meridional (south-north) component of wind at 10 "
            "meters above surface. Positive values indicate wind "
            "from south to north. Unit: m/s."
        ),
    },
    {
        "name": "10m_wind_gust_since_previous_post_processing",
        "description": (
            "Maximum wind gust at 10 meters since the previous "
            "post-processing step, representing extreme short-term "
            "wind speed. Unit: m/s."
        ),
    },
    {
        "name": "instantaneous_10m_wind_gust",
        "description": (
            "Instantaneous wind gust at 10 meters above the "
            "surface, representing peak wind speed at a specific "
            "time. Unit: m/s."
        ),
    },
]

mean_rates_variables = [
    {
        "name": "mean_boundary_layer_dissipation",
        "description": (
            "Mean kinetic energy dissipation rate within the "
            "atmospheric boundary layer. Unit: W/m²."
        ),
    },
    {
        "name": "mean_convective_precipitation_rate",
        "description": (
            "Mean rate of precipitation generated by convective "
            "processes. Unit: kg·m⁻²·s⁻¹ (equivalent to mm/s)."
        ),
    },
    {
        "name": "mean_convective_snowfall_rate",
        "description": (
            "Mean snowfall rate from convective activity. Unit: "
            "kg·m⁻²·s⁻¹ (mm/s of water equivalent)."
        ),
    },
    {
        "name": "mean_eastward_gravity_wave_surface_stress",
        "description": (
            "Mean eastward (zonal) surface stress due to gravity wave drag. "
            "Unit: N/m² (Pa)."
        ),
    },
    {
        "name": "mean_eastward_turbulent_surface_stress",
        "description": (
            "Mean eastward component of surface stress from "
            "turbulent momentum flux. Unit: N/m² (Pa)."
        ),
    },
    {
        "name": "mean_evaporation_rate",
        "description": (
            "Mean rate at which moisture evaporates from the "
            "surface. Unit: kg·m⁻²·s⁻¹ (mm/s water equivalent)."
        ),
    },
    {
        "name": "mean_gravity_wave_dissipation",
        "description": (
            "Mean rate of energy dissipation due to gravity wave breaking. "
            "Unit: W/m²."
        ),
    },
    {
        "name": "mean_large_scale_precipitation_fraction",
        "description": (
            "Mean fraction of total precipitation that is "
            "large-scale (stratiform). Unit: dimensionless (0–1)."
        ),
    },
    {
        "name": "mean_large_scale_precipitation_rate",
        "description": (
            "Mean rate of precipitation from large-scale "
            "(non-convective) processes. Unit: kg·m⁻²·s⁻¹ (mm/s)."
        ),
    },
    {
        "name": "mean_large_scale_snowfall_rate",
        "description": (
            "Mean snowfall rate from large-scale lifting processes. "
            "Unit: kg·m⁻²·s⁻¹ (mm/s water equivalent)."
        ),
    },
    {
        "name": "mean_northward_gravity_wave_surface_stress",
        "description": (
            "Mean northward (meridional) surface stress from "
            "gravity wave drag. Unit: N/m² (Pa)."
        ),
    },
    {
        "name": "mean_northward_turbulent_surface_stress",
        "description": (
            "Mean northward component of turbulent surface momentum stress. "
            "Unit: N/m² (Pa)."
        ),
    },
    {
        "name": "mean_potential_evaporation_rate",
        "description": (
            "Mean potential evaporation under unlimited moisture "
            "supply. Unit: kg·m⁻²·s⁻¹ (mm/s)."
        ),
    },
    {
        "name": "mean_runoff_rate",
        "description": (
            "Mean runoff rate from land surface processes. Unit: "
            "kg·m⁻²·s⁻¹ (equivalent to mm/s)."
        ),
    },
    {
        "name": "mean_snow_evaporation_rate",
        "description": (
            "Mean rate of moisture loss from snow via evaporation "
            "or sublimation. Unit: kg·m⁻²·s⁻¹ (mm/s)."
        ),
    },
    {
        "name": "mean_snowfall_rate",
        "description": (
            "Mean total snowfall rate (convective + large scale). "
            "Unit: kg·m⁻²·s⁻¹ (mm/s water equivalent)."
        ),
    },
    {
        "name": "mean_snowmelt_rate",
        "description": (
            "Mean rate at which snow is melting at the surface. "
            "Unit: kg·m⁻²·s⁻¹ (mm/s water equivalent)."
        ),
    },
    {
        "name": "mean_sub_surface_runoff_rate",
        "description": (
            "Mean rate of subsurface (percolation) runoff. " "Unit: kg·m⁻²·s⁻¹ (mm/s)."
        ),
    },
    {
        "name": "mean_surface_direct_short_wave_radiation_flux",
        "description": (
            "Mean downwelling direct solar radiation at the surface. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_direct_short_wave_radiation_flux_clear_sky",
        "description": (
            "Same as above but estimated under clear-sky conditions (no "
            "clouds). Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_downward_long_wave_radiation_flux",
        "description": (
            "Mean downward infrared (long-wave) radiation reaching the "
            "surface. Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_downward_long_wave_radiation_flux_clear_sky",
        "description": (
            "Clear-sky estimate of downward long-wave radiation. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_downward_short_wave_radiation_flux",
        "description": (
            "Mean total downwelling solar (short-wave) radiation at "
            "surface. Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_downward_short_wave_radiation_flux_clear_sky",
        "description": ("Clear-sky downwelling solar radiation. Unit: W/m²."),
    },
    {
        "name": "mean_surface_downward_uv_radiation_flux",
        "description": (
            "Mean downwelling ultraviolet radiation flux at the surface. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_latent_heat_flux",
        "description": (
            "Mean latent heat flux due to evaporation/sublimation at "
            "surface. Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_net_long_wave_radiation_flux",
        "description": (
            "Mean net (downward minus upward) long-wave radiation "
            "at the surface. Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_net_long_wave_radiation_flux_clear_sky",
        "description": (
            "Clear-sky net long-wave radiation at the surface. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_net_short_wave_radiation_flux",
        "description": (
            "Mean net (downward minus reflected) solar radiation at the "
            "surface. Unit: W/m²."
        ),
    },
    {
        "name": "mean_surface_net_short_wave_radiation_flux_clear_sky",
        "description": ("Clear-sky net short‑wave radiation. Unit: W/m²."),
    },
    {
        "name": "mean_surface_runoff_rate",
        "description": (
            "Mean total surface runoff (overland flow) rate. " "Unit: kg·m⁻²·s⁻¹."
        ),
    },
    {
        "name": "mean_surface_sensible_heat_flux",
        "description": (
            "Mean sensible heat flux (thermal conduction/convection) at "
            "surface. Unit: W/m²."
        ),
    },
    {
        "name": "mean_top_downward_short_wave_radiation_flux",
        "description": (
            "Mean downwelling solar radiation at top of atmosphere. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_top_net_long_wave_radiation_flux",
        "description": (
            "Mean net long-wave radiation at top of atmosphere. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_top_net_long_wave_radiation_flux_clear_sky",
        "description": (
            "Clear-sky net long-wave radiation at the top of atmosphere. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_top_net_short_wave_radiation_flux",
        "description": ("Mean net solar radiation at top of atmosphere. Unit: W/m²."),
    },
    {
        "name": "mean_top_net_short_wave_radiation_flux_clear_sky",
        "description": (
            "Clear-sky net short-wave radiation at top of atmosphere. " "Unit: W/m²."
        ),
    },
    {
        "name": "mean_total_precipitation_rate",
        "description": (
            "Mean total precipitation rate (convective + "
            "stratiform). Unit: kg·m⁻²·s⁻¹ (mm/s)."
        ),
    },
    {
        "name": "mean_vertically_integrated_moisture_divergence",
        "description": (
            "Mean divergence of vertically integrated "
            "moisture—indicating moisture transport convergence "
            "(positive) or divergence (negative). Unit: kg·m⁻²·s⁻¹."
        ),
    },
]

heat_and_radiation_variables = [
    {
        "name": "clear_sky_direct_solar_radiation_at_surface",
        "description": (
            "Direct component of solar radiation reaching the "
            "surface under clear-sky (no clouds) conditions. Unit: "
            "W/m²."
        ),
    },
    {
        "name": "downward_uv_radiation_at_the_surface",
        "description": (
            "Downward flux of ultraviolet (UV) radiation at the "
            "Earth's surface, including both UV-A and UV-B. Unit: "
            "W/m²."
        ),
    },
    {
        "name": "forecast_logarithm_of_surface_roughness_for_heat",
        "description": (
            "Logarithm of the heat-exchange surface roughness "
            "length used for forecasting sensible heat fluxes. "
            "Unit: dimensionless (log‑m)."
        ),
    },
    {
        "name": "instantaneous_surface_sensible_heat_flux",
        "description": (
            "Instantaneous sensible heat flux at the surface, "
            "representing turbulent heat exchange between surface "
            "and atmosphere. Unit: W/m²."
        ),
    },
    {
        "name": "near_ir_albedo_for_diffuse_radiation",
        "description": (
            "Surface albedo in the near-infrared spectrum for "
            "diffuse (scattered) radiation. Unit: dimensionless "
            "(fraction)."
        ),
    },
    {
        "name": "near_ir_albedo_for_direct_radiation",
        "description": (
            "Surface albedo in the near-infrared spectrum for "
            "direct (beam) radiation. Unit: dimensionless "
            "(fraction)."
        ),
    },
    {
        "name": "surface_latent_heat_flux",
        "description": (
            "Latent heat flux at the surface "
            "from evaporation or sublimation. Unit: W/m²."
        ),
    },
    {
        "name": "surface_net_solar_radiation",
        "description": (
            "Net solar (short-wave) radiation at the surface "
            "(downward minus reflected). Unit: W/m²."
        ),
    },
    {
        "name": "surface_net_solar_radiation_clear_sky",
        "description": (
            "Net surface solar radiation " "under clear-sky conditions. Unit: W/m²."
        ),
    },
    {
        "name": "surface_net_thermal_radiation",
        "description": (
            "Net thermal (long-wave) radiation at the surface "
            "(downward minus upward). Unit: W/m²."
        ),
    },
    {
        "name": "surface_net_thermal_radiation_clear_sky",
        "description": (
            "Net surface thermal radiation " "under clear-sky conditions. Unit: W/m²."
        ),
    },
    {
        "name": "surface_sensible_heat_flux",
        "description": (
            "Sensible heat flux at the "
            "surface (turbulent heat exchange). Unit: W/m²."
        ),
    },
    {
        "name": "surface_solar_radiation_downward_clear_sky",
        "description": (
            "Downward solar radiation at the "
            "surface under clear-sky conditions. Unit: W/m²."
        ),
    },
    {
        "name": "surface_solar_radiation_downwards",
        "description": (
            "Total downward solar (short-wave) radiation " "at the surface. Unit: W/m²."
        ),
    },
    {
        "name": "surface_thermal_radiation_downward_clear_sky",
        "description": (
            "Downward thermal (long-wave) radiation at the surface "
            "under clear-sky conditions. Unit: W/m²."
        ),
    },
    {
        "name": "surface_thermal_radiation_downwards",
        "description": (
            "Total downward thermal (long-wave) radiation "
            "at the surface. Unit: W/m²."
        ),
    },
    {
        "name": "toa_incident_solar_radiation",
        "description": (
            "Incident solar radiation at the top of the atmosphere "
            "(above atmosphere). Unit: W/m²."
        ),
    },
    {
        "name": "top_net_solar_radiation",
        "description": (
            "Net solar radiation at the top of the atmosphere "
            "(incoming minus reflected). Unit: W/m²."
        ),
    },
    {
        "name": "top_net_solar_radiation_clear_sky",
        "description": (
            "Net solar radiation at the top of atmosphere under "
            "clear-sky conditions. Unit: W/m²."
        ),
    },
    {
        "name": "top_net_thermal_radiation",
        "description": (
            "Net thermal (long-wave) radiation at the top of the "
            "atmosphere (outgoing minus incoming). Unit: W/m²."
        ),
    },
    {
        "name": "top_net_thermal_radiation_clear_sky",
        "description": (
            "Net thermal radiation at the top of atmosphere under "
            "clear-sky conditions. Unit: W/m²."
        ),
    },
    {
        "name": "total_sky_direct_solar_radiation_at_surface",
        "description": (
            "Direct solar radiation at the surface including all "
            "sky conditions (cloudy or clear). Unit: W/m²."
        ),
    },
    {
        "name": "uv_visible_albedo_for_diffuse_radiation",
        "description": (
            "Surface albedo in the UV-visible range for diffuse "
            "radiation. Unit: dimensionless (fraction)."
        ),
    },
    {
        "name": "uv_visible_albedo_for_direct_radiation",
        "description": (
            "Surface albedo in the UV-visible range for direct "
            "radiation. Unit: dimensionless (fraction)."
        ),
    },
]

cloud_variables = [
    {
        "name": "cloud_base_height",
        "description": (
            "Height of the cloud base above ground level. It "
            "indicates the lowest altitude at which clouds are "
            "present. Unit: meters (m)."
        ),
    },
    {
        "name": "high_cloud_cover",
        "description": (
            "Fraction of the sky covered by high-level clouds "
            "(typically above ~6 km altitude). Unit: dimensionless "
            "(0 to 1)."
        ),
    },
    {
        "name": "low_cloud_cover",
        "description": (
            "Fraction of the sky covered by low-level clouds "
            "(typically below ~2 km altitude). Unit: dimensionless "
            "(0 to 1)."
        ),
    },
    {
        "name": "medium_cloud_cover",
        "description": (
            "Fraction of the sky covered by mid-level clouds "
            "(typically between 2–6 km altitude). Unit: "
            "dimensionless (0 to 1)."
        ),
    },
    {
        "name": "total_cloud_cover",
        "description": (
            "Fraction of the sky covered by all clouds (low + "
            "medium + high). Unit: dimensionless (0 to 1)."
        ),
    },
    {
        "name": "total_column_cloud_ice_water",
        "description": (
            "Total mass of cloud ice water in a vertical column "
            "from surface to top of the atmosphere. Unit: kg/m²."
        ),
    },
    {
        "name": "total_column_cloud_liquid_water",
        "description": (
            "Total mass of cloud liquid water in a vertical column "
            "from surface to top of the atmosphere. Unit: kg/m²."
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_cloud_frozen_water_flux",
        "description": (
            "Vertically integrated divergence of frozen (ice) cloud "
            "water flux. It quantifies horizontal spreading of ice "
            "water. Unit: kg/(m²·s)."
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_cloud_liquid_water_flux",
        "description": (
            "Vertically integrated divergence of cloud liquid water "
            "flux, indicating where cloud water is spreading out "
            "horizontally. Unit: kg/(m²·s)."
        ),
    },
    {
        "name": "vertical_integral_of_eastward_cloud_frozen_water_flux",
        "description": (
            "Vertically integrated flux of cloud ice water "
            "transported eastward. Unit: kg/(m·s)."
        ),
    },
    {
        "name": "vertical_integral_of_eastward_cloud_liquid_water_flux",
        "description": (
            "Vertically integrated flux of cloud liquid water "
            "transported eastward. Unit: kg/(m·s)."
        ),
    },
    {
        "name": "vertical_integral_of_northward_cloud_frozen_water_flux",
        "description": (
            "Vertically integrated flux of cloud ice water "
            "transported northward. Unit: kg/(m·s)."
        ),
    },
    {
        "name": "vertical_integral_of_northward_cloud_liquid_water_flux",
        "description": (
            "Vertically integrated flux of cloud liquid water "
            "transported northward. Unit: kg/(m·s)."
        ),
    },
]

lake_variables = [
    {
        "name": "lake_bottom_temperature",
        "description": (
            "Temperature at the bottom layer of the lake. Reflects "
            "long-term thermal state. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "lake_cover",
        "description": (
            "Fraction of the grid cell covered by "
            "lake water. Unit: dimensionless (0 to 1)."
        ),
    },
    {
        "name": "lake_depth",
        "description": (
            "Total depth of the lake at " "a given location. Unit: meters (m)."
        ),
    },
    {
        "name": "lake_ice_depth",
        "description": (
            "Depth (thickness) of the ice layer "
            "on the lake surface. Unit: meters (m)."
        ),
    },
    {
        "name": "lake_ice_temperature",
        "description": ("Temperature of the lake's " "ice layer. Unit: Kelvin (K)."),
    },
    {
        "name": "lake_mix_layer_depth",
        "description": (
            "Depth of the upper mixed layer of the lake, where "
            "temperature is relatively uniform due to mixing. Unit: "
            "meters (m)."
        ),
    },
    {
        "name": "lake_mix_layer_temperature",
        "description": (
            "Temperature of the mixed layer " "in the lake. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "lake_shape_factor",
        "description": (
            "Dimensionless parameter describing lake geometry, used "
            "in vertical mixing and energy balance calculations. "
            "Unit: dimensionless."
        ),
    },
    {
        "name": "lake_total_layer_temperature",
        "description": (
            "Average temperature of the entire " "lake water column. Unit: Kelvin (K)."
        ),
    },
]

evaporation_and_runoff_variables = [
    {
        "name": "evaporation",
        "description": (
            "Total actual evaporation from surface (includes soil, "
            "vegetation, water bodies). Negative values represent "
            "upward flux. Unit: meters (m) of water equivalent."
        ),
    },
    {
        "name": "potential_evaporation",
        "description": (
            "Evaporation rate under ideal conditions (no soil "
            "moisture limitation), often used as a reference. Unit: "
            "meters (m) of water equivalent."
        ),
    },
    {
        "name": "runoff",
        "description": (
            "Total runoff (surface + subsurface) reaching rivers or "
            "streams. Unit: meters (m) of water equivalent."
        ),
    },
    {
        "name": "sub_surface_runoff",
        "description": (
            "Runoff from below the surface, including percolation "
            "and lateral soil water flow. Unit: meters (m) of water "
            "equivalent."
        ),
    },
    {
        "name": "surface_runoff",
        "description": (
            "Overland flow that occurs when rainfall exceeds "
            "infiltration capacity. Unit: meters (m) of water "
            "equivalent."
        ),
    },
]

precipitation_variables = [
    {
        "name": "convective_precipitation",
        "description": (
            "Total precipitation from convective processes "
            "(showers, thunderstorms). Unit: meters (m) of water "
            "equivalent."
        ),
    },
    {
        "name": "convective_rain_rate",
        "description": (
            "Rainfall rate from convective precipitation. "
            "Unit: meters per second (m/s)."
        ),
    },
    {
        "name": "instantaneous_large_scale_surface_precipitation_fraction",
        "description": (
            "Fraction of grid cell area receiving large-scale "
            "precipitation at a given time. Unit: (0 to 1, "
            "dimensionless)."
        ),
    },
    {
        "name": "large_scale_rain_rate",
        "description": (
            "Rainfall rate from stratiform (large-scale) "
            "precipitation. Unit: meters per second (m/s)."
        ),
    },
    {
        "name": "large_scale_precipitation",
        "description": (
            "Total precipitation from large-scale (non-convective) "
            "processes. Unit: meters (m) of water equivalent."
        ),
    },
    {
        "name": "large_scale_precipitation_fraction",
        "description": (
            "Fraction of the grid cell receiving large-scale "
            "precipitation. Unit: (0 to 1, dimensionless)."
        ),
    },
    {
        "name": ("maximum_total_precipitation_rate_since_previous_post_processing"),
        "description": (
            "Maximum observed total precipitation rate since last "
            "processing step. Unit: meters per second (m/s)."
        ),
    },
    {
        "name": ("minimum_total_precipitation_rate_since_previous_post_processing"),
        "description": (
            "Minimum observed total precipitation rate since last "
            "processing step. Unit: meters per second (m/s)."
        ),
    },
    {
        "name": "precipitation_type",
        "description": (
            "Coded indicator of precipitation type (e.g., rain, "
            "snow). Unit: dimensionless (coded integers)."
        ),
    },
    {
        "name": "total_column_rain_water",
        "description": (
            "Vertically integrated mass of liquid rainwater in a "
            "column of atmosphere. Unit: kilograms per square meter "
            "(kg/m²)."
        ),
    },
    {
        "name": "total_precipitation",
        "description": (
            "Cumulative precipitation (convective + large-scale). "
            "Unit: meters (m) of water equivalent."
        ),
    },
]

snow_variables = [
    {
        "name": "convective_snowfall",
        "description": (
            "Snowfall due to convective processes. "
            "Unit: meters (m) of water equivalent."
        ),
    },
    {
        "name": "convective_snowfall_rate_water_equivalent",
        "description": (
            "Rate of convective snowfall (as water equivalent). "
            "Unit: meters per second (m/s)."
        ),
    },
    {
        "name": "large_scale_snowfall_rate_water_equivalent",
        "description": (
            "Rate of stratiform (large-scale) snowfall (as water "
            "equivalent). Unit: meters per second (m/s)."
        ),
    },
    {
        "name": "large_scale_snowfall",
        "description": (
            "Snowfall due to large-scale (non-convective) "
            "processes. Unit: meters (m) of water equivalent."
        ),
    },
    {
        "name": "snow_albedo",
        "description": (
            "Reflectivity (albedo) of snow-covered surfaces. "
            "Unit: dimensionless (0 to 1)."
        ),
    },
    {
        "name": "snow_density",
        "description": ("Density of snow. Unit: " "kilograms per cubic meter (kg/m³)."),
    },
    {
        "name": "snow_depth",
        "description": "Depth of snow on the surface. Unit: meters (m).",
    },
    {
        "name": "snow_evaporation",
        "description": (
            "Amount of snow lost to evaporation/sublimation. Unit: "
            "meters (m) of water equivalent."
        ),
    },
    {
        "name": "snowfall",
        "description": (
            "Total snowfall (convective + large-scale). Unit: "
            "meters (m) of water equivalent."
        ),
    },
    {
        "name": "snowmelt",
        "description": (
            "Snow that has melted. Unit: " "meters (m) of water equivalent."
        ),
    },
    {
        "name": "temperature_of_snow_layer",
        "description": (
            "Temperature of the snow layer " "at the surface. Unit: Kelvin (K)."
        ),
    },
    {
        "name": "total_column_snow_water",
        "description": (
            "Total mass of snow water in a vertical atmospheric "
            "column. Unit: kilograms per square meter (kg/m²)."
        ),
    },
]

soil_variables = [
    {
        "name": "soil_temperature_level_1",
        "description": (
            "Soil temperature in the topmost " "layer (0–7 cm). Unit: Kelvin (K)."
        ),
    },
    {
        "name": "soil_temperature_level_2",
        "description": (
            "Soil temperature in the second " "layer (7–28 cm). Unit: Kelvin (K)."
        ),
    },
    {
        "name": "soil_temperature_level_3",
        "description": (
            "Soil temperature in the third " "layer (28–100 cm). Unit: Kelvin (K)."
        ),
    },
    {
        "name": "soil_temperature_level_4",
        "description": (
            "Soil temperature in the deepest " "layer (100–289 cm). Unit: Kelvin (K)."
        ),
    },
    {
        "name": "soil_type",
        "description": (
            "Categorical soil type based on " "FAO classification. Unit: integer code."
        ),
    },
    {
        "name": "volumetric_soil_water_layer_1",
        "description": (
            "Volumetric soil moisture in top layer (0–7 cm). Unit: "
            "m³/m³ (volume of water per volume of soil)."
        ),
    },
    {
        "name": "volumetric_soil_water_layer_2",
        "description": (
            "Volumetric soil moisture in second " "layer (7–28 cm). Unit: m³/m³."
        ),
    },
    {
        "name": "volumetric_soil_water_layer_3",
        "description": (
            "Volumetric soil moisture in third " "layer (28–100 cm). Unit: m³/m³."
        ),
    },
    {
        "name": "volumetric_soil_water_layer_4",
        "description": (
            "Volumetric soil moisture in fourth " "layer (100–289 cm). Unit: m³/m³."
        ),
    },
]

vertical_integral_variables = [
    {
        "name": "vertical_integral_of_divergence_of_cloud_frozen_water_flux",
        "description": (
            "Divergence of vertically integrated cloud "
            "frozen water flux. Unit: kg·m⁻²·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_cloud_liquid_water_flux",
        "description": (
            "Divergence of vertically integrated cloud "
            "liquid water flux. Unit: kg·m⁻²·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_geopotential_flux",
        "description": (
            "Divergence of geopotential flux vertically integrated "
            "over the atmosphere. Unit: m²·s⁻³"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_kinetic_energy_flux",
        "description": (
            "Divergence of kinetic energy " "flux integrated vertically. Unit: W/m²"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_mass_flux",
        "description": (
            "Divergence of atmospheric mass "
            "flux integrated vertically. Unit: kg·m⁻²·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_moisture_flux",
        "description": (
            "Divergence of moisture flux integrated over the entire "
            "atmosphere. Unit: kg·m⁻²·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_ozone_flux",
        "description": (
            "Divergence of ozone flux " "vertically integrated. Unit: kg·m⁻²·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_thermal_energy_flux",
        "description": (
            "Divergence of thermal energy " "flux integrated vertically. Unit: W/m²"
        ),
    },
    {
        "name": "vertical_integral_of_divergence_of_total_energy_flux",
        "description": (
            "Divergence of total energy " "flux integrated vertically. Unit: W/m²"
        ),
    },
    {
        "name": "vertical_integral_of_eastward_cloud_frozen_water_flux",
        "description": (
            "Eastward flux of frozen cloud "
            "water integrated vertically. Unit: kg·m⁻¹·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_eastward_cloud_liquid_water_flux",
        "description": (
            "Eastward flux of liquid cloud "
            "water integrated vertically. Unit: kg·m⁻¹·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_eastward_geopotential_flux",
        "description": "Eastward flux of geopotential energy. Unit: m³·s⁻²",
    },
    {
        "name": "vertical_integral_of_eastward_heat_flux",
        "description": "Eastward heat flux vertically integrated. Unit: W/m",
    },
    {
        "name": "vertical_integral_of_eastward_kinetic_energy_flux",
        "description": (
            "Eastward kinetic energy flux " "vertically integrated. Unit: W/m"
        ),
    },
    {
        "name": "vertical_integral_of_eastward_mass_flux",
        "description": "Eastward flux of atmospheric mass. Unit: kg·m⁻¹·s⁻¹",
    },
    {
        "name": "vertical_integral_of_eastward_ozone_flux",
        "description": (
            "Eastward ozone mass flux " "integrated vertically. Unit: kg·m⁻¹·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_eastward_total_energy_flux",
        "description": (
            "Eastward flux of total " "energy vertically integrated. Unit: W/m"
        ),
    },
    {
        "name": "vertical_integral_of_eastward_water_vapour_flux",
        "description": (
            "Eastward flux of water " "vapour integrated vertically. Unit: kg·m⁻¹·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_energy_conversion",
        "description": (
            "Energy conversion term integrated " "over atmosphere. Unit: W/m²"
        ),
    },
    {
        "name": "vertical_integral_of_kinetic_energy",
        "description": (
            "Kinetic energy vertically integrated "
            "over atmospheric column. Unit: J/m²"
        ),
    },
    {
        "name": "vertical_integral_of_mass_of_atmosphere",
        "description": "Total atmospheric mass per unit area. Unit: kg/m²",
    },
    {
        "name": "vertical_integral_of_mass_tendency",
        "description": "Rate of change of atmospheric mass. Unit: kg·m⁻²·s⁻¹",
    },
    {
        "name": "vertical_integral_of_northward_cloud_frozen_water_flux",
        "description": ("Northward flux of frozen " "cloud water. Unit: kg·m⁻¹·s⁻¹"),
    },
    {
        "name": "vertical_integral_of_northward_cloud_liquid_water_flux",
        "description": ("Northward flux of liquid " "cloud water. Unit: kg·m⁻¹·s⁻¹"),
    },
    {
        "name": "vertical_integral_of_northward_geopotential_flux",
        "description": "Northward geopotential flux. Unit: m³·s⁻²",
    },
    {
        "name": "vertical_integral_of_northward_heat_flux",
        "description": "Northward heat energy flux. Unit: W/m",
    },
    {
        "name": "vertical_integral_of_northward_kinetic_energy_flux",
        "description": "Northward kinetic energy flux. Unit: W/m",
    },
    {
        "name": "vertical_integral_of_northward_mass_flux",
        "description": "Northward atmospheric mass flux. Unit: kg·m⁻¹·s⁻¹",
    },
    {
        "name": "vertical_integral_of_northward_ozone_flux",
        "description": (
            "Northward ozone flux " "vertically integrated. Unit: kg·m⁻¹·s⁻¹"
        ),
    },
    {
        "name": "vertical_integral_of_northward_total_energy_flux",
        "description": "Northward total energy flux. Unit: W/m",
    },
    {
        "name": "vertical_integral_of_northward_water_vapour_flux",
        "description": "Northward flux of water vapour. Unit: kg·m⁻¹·s⁻¹",
    },
    {
        "name": "vertical_integral_of_potential_and_internal_energy",
        "description": (
            "Vertically integrated potential and " "internal energy. Unit: J/m²"
        ),
    },
    {
        "name": "vertical_integral_of_potential_internal_and_latent_energy",
        "description": (
            "Vertically integrated sum of potential, "
            "internal, and latent energy. Unit: J/m²"
        ),
    },
    {
        "name": "vertical_integral_of_temperature",
        "description": (
            "Vertical integral of temperature " "over atmospheric column. Unit: K·m"
        ),
    },
    {
        "name": "vertical_integral_of_thermal_energy",
        "description": (
            "Thermal energy integrated over " "the full column. Unit: J/m²"
        ),
    },
    {
        "name": "vertical_integral_of_total_energy",
        "description": (
            "Total energy (kinetic + thermal "
            "+ potential) integrated vertically. Unit: J/m²"
        ),
    },
    {
        "name": "vertically_integrated_moisture_divergence",
        "description": (
            "Divergence of vertically integrated "
            "atmospheric moisture. Unit: kg·m⁻²·s⁻¹"
        ),
    },
]

vegetation_variables = [
    {
        "name": "high_vegetation_cover",
        "description": (
            "Fraction of ground covered by "
            "high vegetation (e.g. forests). Unit: (0–1)"
        ),
    },
    {
        "name": "leaf_area_index_high_vegetation",
        "description": (
            "Leaf area index (LAI) for high vegetation, "
            "representing total leaf area per unit ground area. "
            "Unit: m²/m²"
        ),
    },
    {
        "name": "leaf_area_index_low_vegetation",
        "description": (
            "Leaf area index for low " "vegetation (e.g. grasses, shrubs). Unit: m²/m²"
        ),
    },
    {
        "name": "low_vegetation_cover",
        "description": ("Fraction of ground covered " "by low vegetation. Unit: (0–1)"),
    },
    {
        "name": "type_of_high_vegetation",
        "description": (
            "Classification of high vegetation type (e.g. "
            "broadleaf, needleleaf). Unit: code (integer class)"
        ),
    },
    {
        "name": "type_of_low_vegetation",
        "description": (
            "Classification of low vegetation type (e.g. grassland, "
            "shrubland). Unit: code (integer class)"
        ),
    },
]

ocean_wave_variables = [
    {
        "name": "air_density_over_the_oceans",
        "description": "Density of air at the ocean surface. Unit: kg/m³",
    },
    {
        "name": "coefficient_of_drag_with_waves",
        "description": (
            "Coefficient representing drag between "
            "atmosphere and waves. Unit: dimensionless"
        ),
    },
    {
        "name": "free_convective_velocity_over_the_oceans",
        "description": (
            "Characteristic velocity of " "convective turbulence. Unit: m/s"
        ),
    },
    {
        "name": "maximum_individual_wave_height",
        "description": "Maximum wave height in a wave spectrum. Unit: m",
    },
    {
        "name": "mean_direction_of_total_swell",
        "description": (
            "Average direction from which swell is "
            "coming. Unit: degrees (0° = north)"
        ),
    },
    {
        "name": "mean_direction_of_wind_waves",
        "description": "Mean direction of wind-generated waves. Unit: degrees",
    },
    {
        "name": "mean_period_of_total_swell",
        "description": "Mean time interval between swell wave crests. Unit: s",
    },
    {
        "name": "mean_period_of_wind_waves",
        "description": "Mean wave period of wind-generated waves. Unit: s",
    },
    {
        "name": "mean_square_slope_of_waves",
        "description": "Mean square of the wave slope. Unit: dimensionless",
    },
    {
        "name": "mean_wave_direction",
        "description": "Average direction of all waves. Unit: degrees",
    },
    {
        "name": "mean_wave_direction_of_first_swell_partition",
        "description": "Direction of first swell component. Unit: degrees",
    },
    {
        "name": "mean_wave_direction_of_second_swell_partition",
        "description": "Direction of second swell component. Unit: degrees",
    },
    {
        "name": "mean_wave_direction_of_third_swell_partition",
        "description": "Direction of third swell component. Unit: degrees",
    },
    {
        "name": "mean_wave_period",
        "description": "Mean wave period of the total wave field. Unit: s",
    },
    {
        "name": "mean_wave_period_based_on_first_moment",
        "description": ("Mean wave period based on " "spectral first moment. Unit: s"),
    },
    {
        "name": "mean_wave_period_based_on_first_moment_for_swell",
        "description": "Mean period of swell based on first moment. Unit: s",
    },
    {
        "name": "mean_wave_period_based_on_first_moment_for_wind_waves",
        "description": ("Mean period of wind waves " "based on first moment. Unit: s"),
    },
    {
        "name": "mean_wave_period_based_on_second_moment_for_swell",
        "description": "Mean period of swell based on second moment. Unit: s",
    },
    {
        "name": "mean_wave_period_based_on_second_moment_for_wind_waves",
        "description": ("Mean period of wind waves " "based on second moment. Unit: s"),
    },
    {
        "name": "mean_wave_period_of_first_swell_partition",
        "description": "Mean period of first swell component. Unit: s",
    },
    {
        "name": "mean_wave_period_of_second_swell_partition",
        "description": "Mean period of second swell component. Unit: s",
    },
    {
        "name": "mean_wave_period_of_third_swell_partition",
        "description": "Mean period of third swell component. Unit: s",
    },
    {
        "name": "mean_zero_crossing_wave_period",
        "description": ("Mean time between successive " "wave zero-crossings. Unit: s"),
    },
    {
        "name": "model_bathymetry",
        "description": "Ocean depth used in the model. Unit: m",
    },
    {
        "name": "normalized_energy_flux_into_ocean",
        "description": (
            "Normalized rate of energy transfer "
            "into ocean by waves. Unit: dimensionless"
        ),
    },
    {
        "name": "normalized_energy_flux_into_waves",
        "description": (
            "Normalized rate of energy input " "into wave field. Unit: dimensionless"
        ),
    },
    {
        "name": "normalized_stress_into_ocean",
        "description": ("Normalized surface stress " "into ocean. Unit: dimensionless"),
    },
    {
        "name": "ocean_surface_stress_equivalent_10m_neutral_wind_direction",
        "description": (
            "Equivalent wind direction (neutral stability) at 10 m "
            "affecting ocean surface. Unit: degrees"
        ),
    },
    {
        "name": "ocean_surface_stress_equivalent_10m_neutral_wind_speed",
        "description": (
            "Equivalent 10 m wind speed "
            "under neutral stability conditions. Unit: m/s"
        ),
    },
    {
        "name": "peak_wave_period",
        "description": "Period corresponding to peak wave energy. Unit: s",
    },
    {
        "name": "period_corresponding_to_maximum_individual_wave_height",
        "description": "Wave period at maximum wave height. Unit: s",
    },
    {
        "name": "significant_height_of_combined_wind_waves_and_swell",
        "description": (
            "Significant wave height from combined " "wind waves and swell. Unit: m"
        ),
    },
    {
        "name": "significant_height_of_total_swell",
        "description": "Significant height of total swell. Unit: m",
    },
    {
        "name": "significant_height_of_wind_waves",
        "description": "Significant height of wind-generated waves. Unit: m",
    },
    {
        "name": "significant_wave_height_of_first_swell_partition",
        "description": "Height of first swell component. Unit: m",
    },
    {
        "name": "significant_wave_height_of_second_swell_partition",
        "description": "Height of second swell component. Unit: m",
    },
    {
        "name": "significant_wave_height_of_third_swell_partition",
        "description": "Height of third swell component. Unit: m",
    },
    {
        "name": "wave_spectral_directional_width",
        "description": ("Spread of wave energy " "across directions. Unit: degrees"),
    },
    {
        "name": "wave_spectral_directional_width_for_swell",
        "description": ("Directional spread of swell " "wave energy. Unit: degrees"),
    },
    {
        "name": "wave_spectral_directional_width_for_wind_waves",
        "description": "Directional spread of wind wave energy. Unit: degrees",
    },
    {
        "name": "wave_spectral_kurtosis",
        "description": (
            "Kurtosis of the wave spectrum (peakedness relative to "
            "variance). Unit: dimensionless"
        ),
    },
    {
        "name": "wave_spectral_peakedness",
        "description": (
            "Measure of how peaked the " "wave spectrum is. Unit: dimensionless"
        ),
    },
    {
        "name": "wave_spectral_skewness",
        "description": (
            "Asymmetry of the wave " "spectral distribution. Unit: dimensionless"
        ),
    },
]

other_variables = [
    {
        "name": "angle_of_sub_gridscale_orography",
        "description": "Orientation of sub-grid orography. Unit: radians",
    },
    {
        "name": "anisotropy_of_sub_gridscale_orography",
        "description": (
            "Degree of anisotropy in " "sub-grid orography. Unit: dimensionless"
        ),
    },
    {
        "name": "benjamin_feir_index",
        "description": (
            "Stability index for wave trains related to modulation "
            "instability. Unit: dimensionless"
        ),
    },
    {
        "name": "boundary_layer_dissipation",
        "description": "Turbulent energy loss in boundary layer. Unit: W/m²",
    },
    {
        "name": "boundary_layer_height",
        "description": "Top height of the atmospheric boundary layer. Unit: m",
    },
    {
        "name": "charnock",
        "description": (
            "Charnock parameter relating surface stress to "
            "roughness length over water. Unit: dimensionless"
        ),
    },
    {
        "name": "convective_available_potential_energy",
        "description": "Energy available for convection. Unit: J/kg",
    },
    {
        "name": "convective_inhibition",
        "description": (
            "Energy barrier that must be overcome "
            "for convection to occur. Unit: J/kg"
        ),
    },
    {
        "name": "duct_base_height",
        "description": "Base height of atmospheric ducting layer. Unit: m",
    },
    {
        "name": "eastward_gravity_wave_surface_stress",
        "description": (
            "Zonal stress from gravity waves " "at the surface. Unit: N/m²"
        ),
    },
    {
        "name": "eastward_turbulent_surface_stress",
        "description": "Zonal surface stress from turbulence. Unit: N/m²",
    },
    {
        "name": "forecast_albedo",
        "description": (
            "Forecasted surface albedo " "(reflectivity). Unit: 0–1 (dimensionless)"
        ),
    },
    {
        "name": "forecast_surface_roughness",
        "description": "Forecasted surface roughness length. Unit: m",
    },
    {
        "name": "friction_velocity",
        "description": "Shear velocity indicating surface stress. Unit: m/s",
    },
    {
        "name": "geopotential",
        "description": ("Gravitational potential energy per " "unit mass. Unit: m²/s²"),
    },
    {
        "name": "gravity_wave_dissipation",
        "description": "Dissipation of energy by gravity waves. Unit: W/m²",
    },
    {
        "name": "instantaneous_eastward_turbulent_surface_stress",
        "description": (
            "Instantaneous zonal turbulent stress " "at surface. Unit: N/m²"
        ),
    },
    {
        "name": "instantaneous_moisture_flux",
        "description": "Instantaneous surface moisture flux. Unit: kg/m²/s",
    },
    {
        "name": "instantaneous_northward_turbulent_surface_stress",
        "description": (
            "Instantaneous meridional turbulent stress " "at surface. Unit: N/m²"
        ),
    },
    {
        "name": "k_index",
        "description": (
            "Thunderstorm potential index based on " "temperature and humidity. Unit: K"
        ),
    },
    {
        "name": "land_sea_mask",
        "description": ("Binary mask for land (1) " "or sea (0). Unit: dimensionless"),
    },
    {
        "name": "mean_vertical_gradient_of_refractivity_inside_trapping_layer",
        "description": (
            "Average vertical gradient of refractivity "
            "in ducting layer. Unit: N-units/km"
        ),
    },
    {
        "name": ("minimum_vertical_gradient_of_refractivity_inside_trapping_layer"),
        "description": (
            "Minimum gradient of refractivity " "in trapping layer. Unit: N-units/km"
        ),
    },
    {
        "name": "northward_gravity_wave_surface_stress",
        "description": (
            "Meridional stress from gravity waves " "at the surface. Unit: N/m²"
        ),
    },
    {
        "name": "northward_turbulent_surface_stress",
        "description": "Meridional surface stress from turbulence. Unit: N/m²",
    },
    {
        "name": "sea_ice_cover",
        "description": (
            "Fraction of area covered by " "sea ice. Unit: 0–1 (dimensionless)"
        ),
    },
    {
        "name": "skin_reservoir_content",
        "description": "Water content at surface skin layer. Unit: m",
    },
    {
        "name": "slope_of_sub_gridscale_orography",
        "description": (
            "Average slope of terrain " "below model resolution. Unit: radians"
        ),
    },
    {
        "name": "standard_deviation_of_filtered_subgrid_orography",
        "description": "Filtered subgrid orography variability. Unit: m",
    },
    {
        "name": "standard_deviation_of_orography",
        "description": ("Standard deviation of elevation in " "a grid cell. Unit: m"),
    },
    {
        "name": "total_column_ozone",
        "description": "Total ozone from surface to TOA. Unit: Dobson Units",
    },
    {
        "name": "total_column_supercooled_liquid_water",
        "description": ("Amount of supercooled liquid " "water in column. Unit: kg/m²"),
    },
    {
        "name": "total_column_water",
        "description": (
            "Total water content (vapour + liquid " "+ ice) in column. Unit: kg/m²"
        ),
    },
    {
        "name": "total_column_water_vapour",
        "description": "Total water vapour in vertical column. Unit: kg/m²",
    },
    {
        "name": "total_totals_index",
        "description": ("Thunderstorm index using temperature differences. Unit: K"),
    },
    {
        "name": "trapping_layer_base_height",
        "description": "Bottom height of radio wave trapping layer. Unit: m",
    },
    {
        "name": "trapping_layer_top_height",
        "description": "Top height of trapping layer. Unit: m",
    },
    {
        "name": "u_component_stokes_drift",
        "description": "Zonal component of Stokes drift velocity. Unit: m/s",
    },
    {
        "name": "v_component_stokes_drift",
        "description": ("Meridional component of Stokes drift velocity. Unit: m/s"),
    },
    {
        "name": "zero_degree_level",
        "description": "Altitude where temperature is 0°C. Unit: m",
    },
]
