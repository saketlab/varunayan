#' IMD weather stations with coordinates
#'
#' Gets the India Meteorological Department (IMD) city-weather station list.
#' As an option, it also gets the latitude and longitude of each station. The
#' legacy IMD endpoints give only the station names. The responsive IMD site
#' gives a JSON record for each station (`api/fetchCity_static.php`). This record
#' contains `lat` and `lon`. The function adds these values to the station list.
#' You can use the returned coordinates directly as input to [era5ify_point()].
#' You can also use them to make maps.
#'
#' @param with_coordinates Logical. If `TRUE` (default), the function gets
#'   `latitude` and `longitude` for each station (one request for each station).
#'   If `FALSE`, the function returns only `station_id` and `name`.
#' @param cores Integer. The number of parallel workers that get the
#'   coordinates (the function sends this value to [parallel::mclapply()]). The
#'   default is 4. On Windows, set it to 1.
#' @param ... Not used. This argument is necessary for compatibility with the aliases.
#'
#' @return A `data.frame` with the columns `station_id` and `name`. If
#'   `with_coordinates = TRUE`, the data frame also has the columns `latitude`
#'   and `longitude`. The value is `NA` if IMD has no coordinate for a station.
#'
#' @examples
#' \dontrun{
#' stations <- imd_stations()
#' shimla <- stations[grepl("Shimla", stations$name), ]
#' }
#' @export
imd_stations <- function(with_coordinates = TRUE, cores = 4) {
  ua <- "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
  list_url <- "https://internal.imd.gov.in/pages/city_weather_main_mausam.php"
  api_url <- "https://city.imd.gov.in/citywx/responsive/api/fetchCity_static.php"
  referer <- "https://city.imd.gov.in/citywx/responsive/"

  resp <- httr::GET(list_url, httr::add_headers(`User-Agent` = ua), httr::timeout(30))
  if (httr::status_code(resp) != 200) {
    stop("Cannot get the IMD station list (HTTP ", httr::status_code(resp), ")")
  }
  html <- httr::content(resp, as = "text", encoding = "UTF-8")

  pat <- "<option value='([0-9]{4,6})([^']*)'>"
  hits <- regmatches(html, gregexpr(pat, html, perl = TRUE))[[1]]
  if (length(hits) == 0) stop("Cannot find stations in the IMD city list")
  station_id <- as.integer(sub(pat, "\\1", hits, perl = TRUE))
  name <- tools::toTitleCase(tolower(trimws(sub(pat, "\\2", hits, perl = TRUE))))
  stations <- data.frame(station_id = station_id, name = name, stringsAsFactors = FALSE)
  stations <- stations[!duplicated(stations$station_id), ]
  rownames(stations) <- NULL

  if (!isTRUE(with_coordinates)) {
    return(stations)
  }

  fetch_coord <- function(id) {
    r <- tryCatch(
      httr::POST(
        api_url,
        body = list(ID = id), encode = "form",
        httr::add_headers(`User-Agent` = ua, Referer = referer), httr::timeout(30)
      ),
      error = function(e) NULL
    )
    if (is.null(r) || httr::status_code(r) != 200) {
      return(c(NA_real_, NA_real_))
    }
    d <- tryCatch(
      jsonlite::fromJSON(httr::content(r, as = "text", encoding = "UTF-8")),
      error = function(e) NULL
    )
    if (is.null(d)) {
      return(c(NA_real_, NA_real_))
    }
    rec <- if (is.data.frame(d)) d[1, , drop = FALSE] else as.list(d)
    lat <- suppressWarnings(as.numeric(rec$lat))
    lon <- suppressWarnings(as.numeric(rec$lon))
    if (length(lat) != 1 || length(lon) != 1 || is.na(lat) || is.na(lon) ||
      lat < 6 || lat > 38 || lon < 67 || lon > 99) {
      return(c(NA_real_, NA_real_))
    }
    c(lat, lon)
  }

  coords <- parallel::mclapply(stations$station_id, fetch_coord, mc.cores = cores)
  coord_mat <- do.call(rbind, coords)
  stations$latitude <- coord_mat[, 1]
  stations$longitude <- coord_mat[, 2]
  stations
}
