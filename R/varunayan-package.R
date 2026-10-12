#' @keywords internal
"_PACKAGE"

## usethis namespace: start
#' @import sf
#' @import stars
#' @importFrom data.table .SD .BY := data.table as.data.table setorder setnames year month mday yday fifelse fcase
#' @importFrom dplyr group_by summarise select inner_join across any_of mutate filter
#' @importFrom digest digest
#' @importFrom ecmwfr wf_set_key wf_request wf_get_key
#' @importFrom terra rast extract
#' @importFrom httr GET HEAD POST content headers status_code timeout config
#' @importFrom jsonlite write_json
#' @importFrom lubridate ymd
#' @importFrom magrittr "%>%"
#' @importFrom ncdf4 nc_open nc_close ncvar_get
#' @importFrom rlang .data
#' @importFrom tools R_user_dir file_ext file_path_sans_ext
#' @importFrom utils unzip sessionInfo packageVersion
## usethis namespace: end

# Required for data.table operations
.datatable.aware <- TRUE

# Package startup message - only show CDS setup hint if credentials not found
.onAttach <- function(libname, pkgname) {
  has_creds <- nzchar(Sys.getenv("CDS_API_KEY")) || file.exists(path.expand("~/.cdsapirc"))

  if (!has_creds) {
    packageStartupMessage("varunayan: Configure CDS credentials with setup_cds_credentials()")
    packageStartupMessage("Visit: ", .CDS_KEY_URL)
  }
}

# Package detach cleanup
.onUnload <- function(libpath) {
  # Clean up any temporary files
  temp_files <- list.files(path = tempdir(), pattern = "varunayan_.*\\.(nc|geojson)", full.names = TRUE)
  if (length(x = temp_files) > 0) {
    unlink(x = temp_files)
  }
}
