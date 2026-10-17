#' @keywords internal
"_PACKAGE"

## usethis namespace: start
#' @import sf
#' @import stars
#' @importFrom data.table .SD .N .I .GRP .BY .EACHI := data.table as.data.table setDT setorder setnames year month
#' @importFrom dplyr arrange group_by summarise select semi_join inner_join n across all_of any_of bind_rows distinct mutate filter
#' @importFrom digest digest
#' @importFrom ecmwfr wf_set_key wf_request wf_get_key
#' @importFrom terra rast extract
#' @importFrom httr GET POST content headers status_code timeout config
#' @importFrom jsonlite fromJSON toJSON write_json
#' @importFrom lubridate ymd
#' @importFrom magrittr "%>%"
#' @importFrom ncdf4 nc_open nc_close ncvar_get
#' @importFrom rlang .data %||%
#' @importFrom tools R_user_dir file_ext file_path_sans_ext
#' @importFrom utils unzip sessionInfo packageVersion install.packages
## usethis namespace: end

# data.table operations must have this flag
.datatable.aware <- TRUE

# Startup message. Show the CDS setup hint only if the package cannot find credentials.
.onAttach <- function(libname, pkgname) {
  # Examine the ~/.cdsapirc file first. Most users use this setup.
  cdsapirc <- path.expand("~/.cdsapirc")
  has_creds <- file.exists(cdsapirc)

  # If the file does not exist, also examine the ecmwfr credentials
  if (!has_creds) {
    has_creds <- tryCatch(
      {
        key <- wf_get_key()
        !is.null(key) && nchar(key) > 0
      },
      error = function(e) FALSE
    )
  }

  if (!has_creds) {
    packageStartupMessage("varunayan: Configure CDS credentials with setup_cds_credentials()")
    packageStartupMessage("Refer to: https://cds.climate.copernicus.eu/api-how-to")
  }
}

# Remove temporary files when the package unloads
.onUnload <- function(libpath) {
  # Delete the temporary files
  temp_files <- list.files(path = tempdir(), pattern = "varunayan_.*\\.(nc|geojson)", full.names = TRUE)
  if (length(x = temp_files) > 0) {
    unlink(x = temp_files)
  }
}
