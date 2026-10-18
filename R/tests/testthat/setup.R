# CRAN limits checks to 2 cores
data.table::setDTthreads(2)

# keep tests out of the user's real cache
options(varunayan.cache_dir = file.path(tempdir(), "varunayan-test-cache"))
