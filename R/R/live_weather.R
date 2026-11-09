.live_limits <- list(
  station_km = 25, station_tries = 3L, airport_km = 50, airport_minutes = 90,
  heat_index_min_c = 27
)
.live_timeout <- 20
.metar_url <- "https://aviationweather.gov/api/data/metar"

.live_stop <- function(reason) {
  stop(structure(
    class = c("live_source_unavailable", "error", "condition"),
    list(message = reason, call = NULL)
  ))
}

# keep only the HTTP status; URLs can hold an API key
.live_try <- function(expr) {
  tryCatch(expr, error = function(e) {
    if (inherits(e, "live_source_unavailable")) stop(e)
    code <- regmatches(conditionMessage(e), regexpr("HTTP [0-9]+", conditionMessage(e)))
    .live_stop(if (length(code) == 1) code else "request failed")
  })
}

.live_num <- function(value) {
  if (is.null(value) || length(value) != 1) {
    return(NA_real_)
  }
  suppressWarnings(as.numeric(value))
}

.km <- function(lat1, lon1, lat2, lon2) {
  rad <- pi / 180
  dp <- (lat2 - lat1) * rad
  dl <- (lon2 - lon1) * rad
  a <- sin(dp / 2)^2 + cos(lat1 * rad) * cos(lat2 * rad) * sin(dl / 2)^2
  6371 * 2 * asin(sqrt(a))
}

.live_get_json <- function(url, query = list()) {
  .live_try(.request_json(url, query, .live_timeout))
}

.live_reading <- function(source, kind, site, distance_km, temperature, humidity,
                          wind_speed, wind_direction, observed_at) {
  list(
    source = source, kind = kind, site = site, distance_km = distance_km,
    temperature = temperature, humidity = humidity, wind_speed = wind_speed,
    wind_direction = wind_direction, observed_at = observed_at
  )
}

.live_weatherunion <- function(place) {
  if (!nzchar(Sys.getenv("WEATHERUNION_API_KEY"))) .live_stop("WEATHERUNION_API_KEY is not set")
  stations <- weatherunion_stations(temperature_only = TRUE)
  distances <- .km(place$latitude, place$longitude, stations$latitude, stations$longitude)
  nearest <- utils::head(order(distances), .live_limits$station_tries)
  nearby <- nearest[distances[nearest] <= .live_limits$station_km]
  if (length(nearby) == 0) .live_stop(sprintf("no station within %.0f km", .live_limits$station_km))
  for (index in nearby) {
    row <- .live_try(weatherunion_weather(stations$station_id[index], timeout = .live_timeout))
    if (is.na(row$temperature)) next
    return(.live_reading(
      "weatherunion", "station", paste0(stations$name[index], ", ", stations$city[index]),
      distances[index], row$temperature, row$humidity, row$wind_speed, row$wind_direction,
      as.POSIXct(NA, tz = "UTC")
    ))
  }
  .live_stop(sprintf("none of the %d nearest stations is reporting", length(nearby)))
}

.live_openweathermap <- function(place) {
  key <- Sys.getenv("OPENWEATHERMAP_API_KEY")
  if (!nzchar(key)) .live_stop("OPENWEATHERMAP_API_KEY is not set")
  data <- .live_get_json(
    "https://api.openweathermap.org/data/2.5/weather",
    list(lat = place$latitude, lon = place$longitude, units = "metric", appid = key)
  )
  .live_reading(
    "openweathermap", "model",
    if (is.null(data$name) || !nzchar(data$name)) place$label else data$name,
    NA_real_, .live_num(data$main$temp), .live_num(data$main$humidity),
    .live_num(data$wind$speed), .live_num(data$wind$deg),
    as.POSIXct(data$dt, origin = "1970-01-01", tz = "UTC")
  )
}

# box around the search circle; a degree of latitude is at least 110 km
.metar_bbox <- function(place) {
  lat_box <- .live_limits$airport_km / 110
  lon_box <- lat_box / max(cos(place$latitude * pi / 180), 0.01)
  sprintf(
    "%.2f,%.2f,%.2f,%.2f",
    place$latitude - lat_box, place$longitude - lon_box,
    place$latitude + lat_box, place$longitude + lon_box
  )
}

.live_metar <- function(place) {
  reports <- .live_get_json(.metar_url, list(bbox = .metar_bbox(place), format = "json"))
  now <- as.numeric(Sys.time())
  best <- NULL
  best_km <- Inf
  for (report in reports) {
    if (is.na(.live_num(report$temp)) || is.null(report$obsTime)) next
    km <- .km(place$latitude, place$longitude, report$lat, report$lon)
    if (km <= .live_limits$airport_km && now - report$obsTime <= .live_limits$airport_minutes * 60 && km < best_km) {
      best <- report
      best_km <- km
    }
  }
  if (is.null(best)) .live_stop(sprintf("no recent airport report within %.0f km", .live_limits$airport_km))
  temperature <- as.numeric(best$temp)
  dewpoint <- .live_num(best$dewp)
  .live_reading(
    "metar", "airport", best$name %||% best$icaoId %||% "airport",
    best_km, temperature,
    if (is.na(dewpoint)) NA_real_ else relative_humidity_from_dewpoint(temperature, dewpoint),
    .live_num(best$wspd) * .knots_to_ms, .live_num(best$wdir),
    as.POSIXct(best$obsTime, origin = "1970-01-01", tz = "UTC")
  )
}

.live_metar_any_distance <- function(place) {
  reports <- .live_try(metar_observations())
  age <- as.numeric(difftime(Sys.time(), reports$observed_at, units = "mins"))
  fresh <- reports[!is.na(reports$temperature) & !is.na(age) & age <= .live_limits$airport_minutes, ]
  if (nrow(fresh) == 0) .live_stop("no recent airport report anywhere")
  distances <- .km(place$latitude, place$longitude, fresh$latitude, fresh$longitude)
  index <- which.min(distances)
  row <- fresh[index, ]
  site <- row$station_id
  named <- tryCatch(
    .live_get_json(.metar_url, list(ids = site, format = "json")),
    live_source_unavailable = function(e) list()
  )
  if (length(named) > 0 && !is.null(named[[1]]$name)) site <- named[[1]]$name
  .live_reading(
    "metar", "airport", site, distances[index], row$temperature, row$humidity,
    row$wind_speed, row$wind_direction, row$observed_at
  )
}

.live_metar_nearest <- function(place) {
  tryCatch(.live_metar(place), live_source_unavailable = function(e) .live_metar_any_distance(place))
}

.live_open_meteo <- function(place) {
  row <- .live_try(open_meteo_weather(place$latitude, place$longitude))
  .live_reading(
    "open-meteo", "model", place$label, NA_real_, row$temperature[1], row$humidity[1],
    row$wind_speed[1], row$wind_direction[1], row$datetime[1]
  )
}

.live_sources <- function() {
  list(
    weatherunion = .live_weatherunion,
    openweathermap = .live_openweathermap,
    metar = .live_metar,
    `open-meteo` = .live_open_meteo
  )
}

# geocoder matches prefixes: "Leh" returns Le Havre first
.choose_place <- function(results, name) {
  names_found <- vapply(results, function(hit) tolower(hit$name), character(1))
  exact <- which(names_found == tolower(trimws(name)))
  results[[if (length(exact) > 0) exact[1] else 1L]]
}

.locate <- function(place = NULL, latitude = NULL, longitude = NULL) {
  if (!is.null(latitude) && !is.null(longitude)) {
    return(list(
      latitude = latitude, longitude = longitude,
      label = sprintf("%.3f, %.3f", latitude, longitude)
    ))
  }
  if (!is.null(place) && nzchar(place)) {
    found <- .live_get_json(
      "https://geocoding-api.open-meteo.com/v1/search",
      list(name = place, count = 10)
    )$results
    if (length(found) == 0) .live_stop(sprintf("Cannot find a place called '%s'", place))
    hit <- .choose_place(found, place)
    return(list(
      latitude = hit$latitude, longitude = hit$longitude,
      label = paste(c(hit$name, hit$country), collapse = ", ")
    ))
  }
  data <- .live_get_json("https://ipinfo.io/json")
  if (is.null(data$loc)) .live_stop("IP location is unavailable; pass a place name")
  coords <- as.numeric(strsplit(data$loc, ",")[[1]])
  list(
    latitude = coords[1], longitude = coords[2],
    label = paste0(paste(c(data$city, data$country), collapse = ", "), " (approximate, from IP)")
  )
}

#' Find a place, or find yourself from your IP address
#'
#' With no arguments, the function sends your IP address to ipinfo.io. The
#' result is approximate. A place name is sent to the Open-Meteo geocoder.
#'
#' @param place Place name.
#' @param latitude Latitude. Use with `longitude`.
#' @param longitude Longitude. Use with `latitude`.
#' @param ... Not used. This argument is necessary for compatibility with the aliases.
#'
#' @return A one-row `data.frame` with `latitude`, `longitude` and `label`.
#'
#' @examples
#' \donttest{
#' tryCatch(get_location("Zurich"), error = function(e) message(conditionMessage(e)))
#' }
#' @export
get_location <- function(place = NULL, latitude = NULL, longitude = NULL) {
  as.data.frame(.locate(place, latitude, longitude), stringsAsFactors = FALSE)
}

#' Live weather for a place, or for your IP location
#'
#' Sources are tried from the most local to the least: `"weatherunion"` (needs
#' `WEATHERUNION_API_KEY`), `"openweathermap"` (needs `OPENWEATHERMAP_API_KEY`),
#' `"metar"` (nearest airport within 50 km) and `"open-meteo"`. With
#' `source = "metar"`, an airport at any distance is allowed.
#'
#' @param place Place name. The default is your location, from your IP address.
#' @param latitude Latitude. Use with `longitude`.
#' @param longitude Longitude. Use with `latitude`.
#' @param source `"auto"` or one source name.
#' @param ... Not used. This argument is necessary for compatibility with the aliases.
#'
#' @return A one-row `data.frame`: `place`, `latitude`, `longitude`, `source`,
#'   `kind` (`"station"`, `"airport"` or `"model"`), `site`, `distance_km`,
#'   `temperature` (degrees C), `humidity` (percent), `heat_index` (degrees C),
#'   `wind_speed` (m/s), `wind_direction` (degrees) and `observed_at` (UTC). The
#'   attribute `"skipped"` says why earlier sources were passed.
#'
#' @examples
#' \donttest{
#' tryCatch(
#'   get_current_weather("Zurich", source = "metar"),
#'   error = function(e) message(conditionMessage(e))
#' )
#' }
#' @export
get_current_weather <- function(place = NULL, latitude = NULL, longitude = NULL,
                                source = "auto") {
  sources <- .live_sources()
  if (source != "auto" && !source %in% names(sources)) {
    stop(sprintf("Unknown source '%s'", source))
  }
  where <- .locate(place, latitude, longitude)
  if (source != "auto") sources <- sources[source]
  if (identical(source, "metar")) sources$metar <- .live_metar_nearest

  skipped <- list()
  reading <- NULL
  for (name in names(sources)) {
    reading <- tryCatch(sources[[name]](where), live_source_unavailable = function(e) {
      skipped[[name]] <<- conditionMessage(e)
      NULL
    })
    if (!is.null(reading)) break
  }
  if (is.null(reading)) {
    reasons <- paste(names(skipped), unlist(skipped), sep = ": ", collapse = "; ")
    .live_stop(paste("No source could answer:", reasons))
  }
  heat <- if (is.na(reading$temperature) || is.na(reading$humidity) || reading$temperature < .live_limits$heat_index_min_c) {
    NA_real_
  } else {
    heat_index(reading$temperature, reading$humidity)
  }
  fields <- c(
    list(place = where$label, latitude = where$latitude, longitude = where$longitude),
    append(reading, list(heat_index = heat), after = 6)
  )
  out <- do.call(data.frame, c(fields, stringsAsFactors = FALSE))
  attr(out, "skipped") <- skipped
  out
}
