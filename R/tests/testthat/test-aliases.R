# targets are mocked, so nothing touches the network

alias_map <- c(
  ERA5ifyGeojson = "era5ify_geojson",
  ERA5ifyBbox = "era5ify_bbox",
  ERA5ifyPoint = "era5ify_point",
  IMDRainfallBbox = "imd_rainfall_bbox",
  IMDRainfallGeojson = "imd_rainfall_geojson",
  IMDTemperatureBbox = "imd_temperature_bbox",
  IMDTemperatureGeojson = "imd_temperature_geojson",
  SetupCdsCredentials = "setup_cds_credentials",
  SearchVariable = "search_variable",
  DescribeVariables = "describe_variables",
  ListAvailableVariables = "list_available_variables",
  GetAvailablePressureLevels = "get_available_pressure_levels",
  PopulateSampleCache = "populate_sample_cache",
  ShowCacheInfo = "show_cache_info",
  ClearCache = "clear_cache",
  GetCacheDir = "get_cache_dir",
  GetERA5CountryTemperature = "get_era5_country_temperature",
  HadEX3Bbox = "hadex3_bbox",
  HadEX3Geojson = "hadex3_geojson",
  ListHadEX3Indices = "list_hadex3_indices",
  CRUTSBbox = "cru_ts_bbox",
  CRUTSGeojson = "cru_ts_geojson",
  ListCRUTSVariables = "list_cru_ts_variables",
  CheckSystemReadiness = "check_system_readiness",
  GetPackageInfo = "get_package_info"
)

test_that("every alias is exported and its target exists", {
  ns_exports <- getNamespaceExports("varunayan")
  for (alias in names(alias_map)) {
    expect_true(alias %in% ns_exports, info = alias)
    expect_true(alias_map[[alias]] %in% ns_exports, info = alias_map[[alias]])
    expect_true(is.function(get(alias, envir = asNamespace("varunayan"))), info = alias)
  }
})

test_that("aliases forward positional and named arguments to their targets", {
  ns <- asNamespace("varunayan")
  for (alias in names(alias_map)) {
    target <- alias_map[[alias]]
    mocks <- list()
    mocks[[target]] <- function(...) list(target = target, args = list(...))
    do.call(local_mocked_bindings, c(mocks, list(.env = environment())))

    res <- get(alias, envir = ns)("pos", key = 42, flag = TRUE)
    expect_equal(res$target, target, info = alias)
    expect_equal(res$args, list("pos", key = 42, flag = TRUE), info = alias)

    res0 <- get(alias, envir = ns)()
    expect_equal(res0$args, list(), info = alias)
  }
})

test_that("GetPackageInfo returns session info invisibly without network", {
  msgs <- capture_messages(info <- GetPackageInfo())
  expect_true(any(grepl("varunayan Package Information", msgs)))
  expect_true(any(grepl("^R version: ", msgs)))
  expect_s3_class(info, "sessionInfo")
  expect_invisible(suppressMessages(GetPackageInfo()))
})
