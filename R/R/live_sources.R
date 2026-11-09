.knots_to_ms <- 0.514444
.live_ua <- "varunayan-cli"

.request_json <- function(url, query, timeout) {
  resp <- httr::GET(url, query = query, httr::user_agent(.live_ua), httr::timeout(timeout))
  httr::stop_for_status(resp)
  jsonlite::fromJSON(httr::content(resp, as = "text", encoding = "UTF-8"), simplifyVector = FALSE)
}

.parse_metar <- function(text, prefixes = NULL) {
  lines <- strsplit(text, "\r?\n")[[1]]
  start <- which(startsWith(lines, "raw_text"))[1]
  if (is.na(start)) stop("The METAR file has no header line")
  raw <- utils::read.csv(
    text = paste(lines[start:length(lines)], collapse = "\n"),
    stringsAsFactors = FALSE
  )
  if (!is.null(prefixes)) {
    keep <- Reduce(`|`, lapply(prefixes, function(p) startsWith(raw$station_id, p)))
    raw <- raw[keep, ]
  }
  data.frame(
    station_id = raw$station_id,
    observed_at = as.POSIXct(raw$observation_time, format = "%Y-%m-%dT%H:%M:%S", tz = "UTC"),
    latitude = raw$latitude,
    longitude = raw$longitude,
    temperature = raw$temp_c,
    dewpoint = raw$dewpoint_c,
    humidity = relative_humidity_from_dewpoint(raw$temp_c, raw$dewpoint_c),
    wind_speed = raw$wind_speed_kt * .knots_to_ms,
    wind_direction = suppressWarnings(as.numeric(raw$wind_dir_degrees)),
    raw_text = raw$raw_text,
    stringsAsFactors = FALSE
  )
}

#' Latest METAR airport observations
#'
#' Gets the latest METAR report from each airport. One request fetches every
#' airport, from the NOAA Aviation Weather Center bulk file. No API key is
#' necessary.
#'
#' @param prefixes Character vector. The function keeps airports whose ICAO code
#'   starts with one of these values, for example `c("VA", "VE", "VI", "VO")`
#'   for India. The default `NULL` keeps every airport in the world.
#' @param timeout Request timeout in seconds.
#' @param ... Not used. This argument is necessary for compatibility with the aliases.
#'
#' @return A `data.frame` with one row per airport: `station_id`, `observed_at`
#'   (UTC), `latitude`, `longitude`, `temperature` (degrees C), `dewpoint`
#'   (degrees C), `humidity` (percent), `wind_speed` (m/s), `wind_direction`
#'   (degrees, `NA` when variable) and `raw_text`.
#'
#' @examples
#' \donttest{
#' india <- tryCatch(
#'   metar_observations(c("VA", "VE", "VI", "VO")),
#'   error = function(e) message("METAR server unavailable: ", conditionMessage(e))
#' )
#' }
#' @export
metar_observations <- function(prefixes = NULL, timeout = 60) {
  resp <- httr::GET(
    "https://aviationweather.gov/data/cache/metars.cache.csv.gz",
    httr::user_agent(.live_ua),
    httr::timeout(timeout)
  )
  httr::stop_for_status(resp, task = "get the METAR file")
  body <- httr::content(resp, as = "raw")
  if (length(body) >= 2 && identical(body[1:2], as.raw(c(0x1f, 0x8b)))) {
    body <- memDecompress(body, type = "gzip")
  }
  .parse_metar(rawToChar(body), prefixes)
}

.open_meteo_fields <- c(
  temperature_2m = "temperature",
  relative_humidity_2m = "humidity",
  wind_speed_10m = "wind_speed",
  wind_direction_10m = "wind_direction",
  precipitation = "rainfall"
)

.parse_open_meteo <- function(block, latitude, longitude) {
  times <- unlist(block$time)
  out <- data.frame(
    datetime = as.POSIXct(times, format = "%Y-%m-%dT%H:%M", tz = "UTC"),
    latitude = latitude,
    longitude = longitude
  )
  for (field in names(.open_meteo_fields)) {
    values <- block[[field]]
    out[[.open_meteo_fields[[field]]]] <- if (is.null(values)) {
      NA_real_
    } else {
      vapply(values, .live_num, numeric(1))
    }
  }
  # current rainfall is mm per interval
  if (!is.null(block$interval)) out$rainfall <- out$rainfall * 3600 / unlist(block$interval)[1]
  out
}

#' Open-Meteo weather for a point
#'
#' Gets the current conditions or hourly history for a point from Open-Meteo.
#' These are model values, not measurements. No API key is necessary.
#'
#' @param latitude Latitude of the point.
#' @param longitude Longitude of the point.
#' @param start_date First day of hourly history (`"YYYY-MM-DD"`). Give both
#'   dates or neither. With neither, the result is the current conditions.
#' @param end_date Last day of hourly history (`"YYYY-MM-DD"`).
#' @param timeout Request timeout in seconds.
#' @param ... Not used. This argument is necessary for compatibility with the aliases.
#'
#' @return A `data.frame` with `datetime` (UTC), `latitude`, `longitude`,
#'   `temperature` (degrees C), `humidity` (percent), `wind_speed` (m/s),
#'   `wind_direction` (degrees) and `rainfall` (mm/h).
#'
#' @examples
#' \donttest{
#' now <- tryCatch(
#'   open_meteo_weather(19.09, 72.87),
#'   error = function(e) message("Open-Meteo unavailable: ", conditionMessage(e))
#' )
#' }
#' @export
open_meteo_weather <- function(latitude, longitude, start_date = NULL, end_date = NULL,
                               timeout = 30) {
  if (is.null(start_date) != is.null(end_date)) {
    stop("Give both start_date and end_date, or neither")
  }
  fields <- paste(names(.open_meteo_fields), collapse = ",")
  query <- list(
    latitude = latitude, longitude = longitude,
    wind_speed_unit = "ms", timezone = "UTC"
  )
  current <- is.null(start_date)
  if (current) {
    url <- "https://api.open-meteo.com/v1/forecast"
    query$current <- fields
  } else {
    url <- "https://archive-api.open-meteo.com/v1/archive"
    query$hourly <- fields
    query$start_date <- start_date
    query$end_date <- end_date
  }
  payload <- .request_json(url, query, timeout)
  block <- if (current) lapply(payload$current, list) else payload$hourly
  .parse_open_meteo(block, latitude, longitude)
}
