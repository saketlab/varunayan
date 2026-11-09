#' Weather Union stations
#'
#' Gets the Zomato Weather Union stations that are bundled with the package.
#'
#' @param temperature_only Logical. If `TRUE`, the function keeps only automated
#'   weather stations. Rain gauges report rainfall alone, so temperature and
#'   humidity are always missing for them.
#' @param ... Not used. This argument is necessary for compatibility with the aliases.
#'
#' @return A `data.frame` with the columns `station_id`, `city`, `name`,
#'   `latitude`, `longitude` and `device_type` (`"aws"` or `"rain_gauge"`).
#'
#' @examples
#' stations <- weatherunion_stations(temperature_only = TRUE)
#' head(stations)
#' @export
weatherunion_stations <- function(temperature_only = FALSE) {
  path <- system.file("extdata", "weatherunion_stations.csv", package = "varunayan")
  raw <- utils::read.csv(path, stringsAsFactors = FALSE)
  stations <- data.frame(
    station_id = raw$localityId,
    city = raw$cityName,
    name = raw$localityName,
    latitude = raw$latitude,
    longitude = raw$longitude,
    device_type = ifelse(startsWith(raw$device_type, "1"), "aws", "rain_gauge"),
    stringsAsFactors = FALSE
  )
  if (isTRUE(temperature_only)) {
    stations <- stations[stations$device_type == "aws", ]
    rownames(stations) <- NULL
  }
  stations
}

#' Current observations from Weather Union stations
#'
#' Gets current observations from Zomato Weather Union. Each station costs one
#' request against the API key's daily quota. The API gives no observation
#' time, so `fetched_at` is the UTC time of the request.
#'
#' @param station_ids Character vector of station ids from
#'   [weatherunion_stations()].
#' @param api_key API key. The default is the `WEATHERUNION_API_KEY` environment
#'   variable.
#' @param timeout Request timeout in seconds.
#' @param ... Not used. This argument is necessary for compatibility with the aliases.
#'
#' @return A `data.frame` with one row per station: `station_id`, `fetched_at`,
#'   `temperature` (degrees C), `humidity` (percent), `wind_speed` (m/s),
#'   `wind_direction` (degrees), `rain_intensity` (mm/min) and
#'   `rain_accumulation` (mm since 12 AM IST).
#'
#' @examples
#' \donttest{
#' if (nzchar(Sys.getenv("WEATHERUNION_API_KEY"))) {
#'   weatherunion_weather("ZWL005764")
#' }
#' }
#' @export
weatherunion_weather <- function(station_ids,
                                 api_key = Sys.getenv("WEATHERUNION_API_KEY"),
                                 timeout = 30) {
  if (!nzchar(api_key)) stop("Set WEATHERUNION_API_KEY or pass api_key")
  url <- "https://www.weatherunion.com/gw/weather/external/v0/get_locality_weather_data"
  fields <- c(
    "temperature", "humidity", "wind_speed", "wind_direction",
    "rain_intensity", "rain_accumulation"
  )

  fetch_one <- function(id) {
    resp <- httr::GET(
      url,
      query = list(locality_id = id),
      httr::add_headers(`x-zomato-api-key` = api_key),
      httr::timeout(timeout)
    )
    httr::stop_for_status(resp, task = paste("get Weather Union station", id))
    payload <- jsonlite::fromJSON(httr::content(resp, as = "text", encoding = "UTF-8"))
    if (!identical(as.integer(payload$status), 200L)) {
      stop(id, ": ", payload$message)
    }
    values <- lapply(fields, function(f) .live_num(payload$locality_weather_data[[f]]))
    names(values) <- fields
    data.frame(
      station_id = id,
      fetched_at = as.POSIXct(Sys.time(), tz = "UTC"),
      values,
      stringsAsFactors = FALSE
    )
  }

  do.call(rbind, lapply(station_ids, fetch_one))
}
