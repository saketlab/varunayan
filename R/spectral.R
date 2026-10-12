#' Normalized Difference Vegetation Index
#'
#' `NDVI = (NIR - Red) / (NIR + Red)` from surface reflectance, e.g. Landsat 8-9
#' bands 5 and 4, Sentinel-2 bands 8 and 4, or MODIS bands 2 and 1. Works on
#' numeric vectors and on `terra::SpatRaster` layers.
#'
#' @param nir Near-infrared reflectance.
#' @param red Red reflectance.
#' @return NDVI in the range -1 to 1, the same shape as the inputs.
#' @references Tucker, C.J. (1979). Red and photographic infrared linear
#'   combinations for monitoring vegetation. Remote Sensing of Environment,
#'   8(2), 127-150. \doi{10.1016/0034-4257(79)90013-0}
#' @seealso [ndbi()]
#' @export
#' @examples
#' ndvi(nir = 0.45, red = 0.08)
ndvi <- function(nir, red) (nir - red) / (nir + red)

#' Normalized Difference Built-up Index
#'
#' `NDBI = (SWIR - NIR) / (SWIR + NIR)` from surface reflectance, using the
#' 1.55-1.75 um shortwave infrared band, e.g. Landsat 8-9 bands 6 and 5,
#' Sentinel-2 bands 11 and 8, or Landsat 5 TM bands 5 and 4 as in Zha et al.
#' (2003). Positive values indicate built-up or bare surfaces. Works on numeric
#' vectors and on `terra::SpatRaster` layers.
#'
#' @param swir Shortwave infrared reflectance.
#' @param nir Near-infrared reflectance.
#' @return NDBI in the range -1 to 1, the same shape as the inputs.
#' @references Zha, Y., Gao, J. & Ni, S. (2003). Use of normalized difference
#'   built-up index in automatically mapping urban areas from TM imagery.
#'   International Journal of Remote Sensing, 24(3), 583-594.
#'   \doi{10.1080/01431160304987}
#' @seealso [ndvi()]
#' @export
#' @examples
#' ndbi(swir = 0.30, nir = 0.22)
ndbi <- function(swir, nir) (swir - nir) / (swir + nir)
