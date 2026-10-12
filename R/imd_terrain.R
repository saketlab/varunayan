.terrain_grid <- function() {
  if (is.null(.varunayan_env$imd_terrain)) {
    .varunayan_env$imd_terrain <- readRDS(system.file("extdata", "imd_terrain.rds", package = "varunayan"))
  }
  .varunayan_env$imd_terrain
}

# linear index into the [lon, lat] matrices
.terrain_cell <- function(g, latitude, longitude) {
  n <- nrow(g$elevation_m)
  a <- floor((longitude - g$lon0) / g$res) + 1
  b <- floor((latitude - g$lat0) / g$res) + 1
  ifelse(a >= 1 & a <= n & b >= 1 & b <= n, a + (b - 1) * n, NA_integer_)
}

#' Elevation of locations in India
#'
#' Looks up surface elevation from a 5 arc-minute (about 9 km) grid bundled
#' with the package, covering 6-38 N and 66-98 E. Each value is the median
#' land elevation of the 5 arc-minute cell holding the location, built by
#' `data-raw/imd_terrain.R` from ETOPO 2022 at 60 arc-seconds.
#'
#' @param latitude,longitude Coordinates in decimal degrees.
#' @return Elevation in metres, `NA` over open sea or outside the grid.
#' @references NOAA National Centers for Environmental Information (2022).
#'   ETOPO 2022 15 Arc-Second Global Relief Model. \doi{10.25921/fd45-gt74}
#' @seealso [imd_terrain()]
#' @export
#' @examples
#' # Shimla, Delhi, Leh
#' india_elevation(c(31.10, 28.61, 34.16), c(77.17, 77.21, 77.58))
india_elevation <- function(latitude, longitude) {
  g <- .terrain_grid()
  g$elevation_m[.terrain_cell(g, latitude, longitude)]
}

#' IMD heatwave terrain class of a location
#'
#' Classifies locations as `"hilly"`, `"coastal"` or `"plains"` for the IMD
#' heatwave definition in [heatwave_days()]. IMD sets the Tmax floor by
#' terrain but does not define it. A location is hilly when it lies in Jammu
#' and Kashmir, Ladakh, Himachal Pradesh or Uttarakhand, whose sub-divisions
#' IMD treats as hilly down to the Jammu plains, or when its
#' [india_elevation()] reaches `hill_elevation`, the 1200 m boundary of the
#' mid-hill regions by default. Otherwise it is coastal when land and open sea
#' both lie within about 9 km.
#'
#' For gridded data set `cell_size` to classify whole cells from their Indian
#' land: a cell is hilly when most of it lies in those states or its median
#' elevation reaches `hill_elevation`, and coastal when any of it is.
#'
#' @inheritParams india_elevation
#' @param hill_elevation Elevation (m) at or above which a location is hilly.
#' @param cell_size Grid spacing in degrees when the coordinates are cell
#'   centres, such as 1 for the IMD temperature grid; `NULL` for points.
#' @return A character vector of `"hilly"`, `"coastal"` or `"plains"`, `NA`
#'   outside the grid or over sea.
#' @references NOAA National Centers for Environmental Information (2022).
#'   ETOPO 2022 15 Arc-Second Global Relief Model. \doi{10.25921/fd45-gt74}
#'
#'   Ministry of Panchayati Raj. Local Government Directory district
#'   boundaries, via <https://bharatviz.org>.
#' @seealso [heatwave_days()], [exposure_indicators()]
#' @export
#' @examples
#' # Shimla, Jammu, Delhi, Chennai
#' imd_terrain(c(31.10, 32.73, 28.61, 13.08), c(77.17, 74.86, 77.21, 80.27))
#' # IMD 1 degree cells holding Jammu and Rajkot
#' imd_terrain(c(32.5, 22.5), c(74.5, 70.5), cell_size = 1)
imd_terrain <- function(latitude, longitude, hill_elevation = 1200, cell_size = NULL) {
  g <- .terrain_grid()
  loc <- unique(data.table::data.table(lat = latitude, lon = longitude))
  idx <- if (is.null(cell_size)) {
    as.list(.terrain_cell(g, loc$lat, loc$lon))
  } else {
    s <- seq(-cell_size / 2, cell_size / 2 - g$res, by = g$res) + g$res / 2
    lapply(seq_len(nrow(loc)), function(k) {
      stats::na.omit(.terrain_cell(g, rep(loc$lat[k] + s, each = length(s)), loc$lon[k] + s))
    })
  }
  # the IMD grid interpolates Indian stations only; other land counts where a cell has none
  land <- lapply(idx, function(i) {
    l <- i[!is.na(g$elevation_m[i])]
    if (any(g$india[l])) l[g$india[l]] else l
  })
  elev <- vapply(land, function(l) if (length(l)) stats::median(g$elevation_m[l]) else NA_real_, 0)
  hill <- vapply(land, function(l) isTRUE(mean(g$hill_state[l]) >= 0.5), NA)
  coastal <- vapply(land, function(l) any(g$coastal[l]), NA)
  loc[, terrain := data.table::fcase(
    is.na(elev), NA_character_,
    hill | elev >= hill_elevation, "hilly",
    coastal, "coastal",
    default = "plains"
  )]
  loc[data.table::data.table(lat = latitude, lon = longitude), terrain, on = c("lat", "lon")]
}
