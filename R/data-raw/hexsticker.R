# Make the varunayan logo and its copies for both sites; run from the repo root.
library(ggplot2)
library(sf)
library(hexSticker)

sysfonts::font_add_google("Albert Sans", "albert-sans")
showtext::showtext_auto()

# official LGD boundary, islands included
lgd_url <- "https://geo.bharatviz.org/geojsons/admin/India-geodata-lgd-states.geojson"
sf_use_s2(FALSE)
india <- st_union(st_make_valid(st_read(lgd_url, quiet = TRUE)))
parts <- st_cast(india, "POLYGON")
# exterior rings drop district sliver holes; tiny islands stay unsimplified
parts <- st_sfc(lapply(parts, function(p) st_polygon(p[1])), crs = 4326)
big <- as.numeric(st_area(st_transform(parts, 7755))) > 5e8
parts[big] <- st_simplify(parts[big], dTolerance = 0.05)
india <- st_union(parts)

# ERA5 mean annual rainfall 2000-2024, from R/data-raw/climate_of_india.R:
# each tile is the mean of the 0.25 degree cells inside it, orange dry to blue wet
cells <- st_make_grid(india, cellsize = 0.85, square = TRUE)
cells <- cells[lengths(st_intersects(cells, india)) > 0]
peak <- readRDS("R/inst/extdata/climate_of_india.rds")$peak
pts <- st_as_sf(peak, coords = c("longitude", "latitude"), crs = 4326)
hits <- st_intersects(cells, pts)
# tiles with no cell centre (Lakshadweep) take the nearest cell
empty <- lengths(hits) == 0
hits[empty] <- as.list(st_nearest_feature(st_centroid(cells[empty]), pts))
rain <- vapply(hits, function(i) mean(peak$annual_total[i]), numeric(1))
# rank scaling so the tiles span the full palette
rescale <- function(x) (rank(x) - 1) / (length(x) - 1)
pal <- grDevices::colorRampPalette(
  c("#E4572E", "#F6A945", "#FBE7A1", "#D3ECF8", "#4FB3D9", "#1F5FAD")
)(100)
fill <- pal[1 + round(99 * rescale(rain))]
grid <- st_sf(fill = fill, geometry = cells)

circle <- function(x0, y0, r, n = 90) {
  t <- seq(0, 2 * pi, length.out = n)
  data.frame(x = x0 + r * cos(t), y = y0 + r * sin(t))
}
as_poly <- function(d) st_polygon(list(as.matrix(rbind(d[, c("x", "y")], d[1, c("x", "y")]))))
sun_c <- c(66.1, 16.6)
sun_body <- circle(sun_c[1], sun_c[2], 1.35)
# skip rays hidden by the cloud
ang <- seq(pi / 4, 5 * pi / 4, by = pi / 4)
sun_rays <- data.frame(
  x = sun_c[1] + 1.85 * cos(ang), y = sun_c[2] + 1.85 * sin(ang),
  xend = sun_c[1] + 2.5 * cos(ang), yend = sun_c[2] + 2.5 * sin(ang)
)
cloud <- st_union(st_sfc(
  as_poly(circle(66.3, 14.1, 1.25)),
  as_poly(circle(68.0, 15.0, 1.75)),
  as_poly(circle(69.7, 14.1, 1.15)),
  st_polygon(list(rbind(c(66.3, 12.85), c(69.7, 12.95), c(69.7, 14.1), c(66.3, 14.1), c(66.3, 12.85)))),
  crs = 4326
))
t <- seq(0, 2 * pi, length.out = 80)
drops <- do.call(rbind, lapply(seq_len(3), function(i) {
  x0 <- c(66.6, 68.0, 69.4)[i]
  y0 <- c(11.0, 10.3, 11.0)[i]
  data.frame(x = x0 + 0.5 * sin(t) * sin(t / 2), y = y0 + 0.75 * cos(t), id = i)
}))
wind <- do.call(rbind, lapply(seq_len(2), function(i) {
  x <- seq(62.9, 65.4 - 0.5 * (i == 2), length.out = 40)
  data.frame(x = x, y = 14.2 - 1.15 * (i - 1) + 0.28 * sin((x - 62.9) * 1.6 + i), id = i)
}))

# glyph goes in the empty space above Nepal
k <- 0.82
ctr <- c(67, 14)
dest <- c(86.8, 33.5)
grow <- function(d, cols = c("x", "y")) {
  d[cols[1]] <- dest[1] + k * (d[[cols[1]]] - ctr[1])
  d[cols[2]] <- dest[2] + k * (d[[cols[2]]] - ctr[2])
  d
}
sun_body <- grow(sun_body)
sun_rays <- grow(grow(sun_rays), c("xend", "yend"))
drops <- grow(drops)
wind <- grow(wind)
cloud <- st_sfc((st_geometry(cloud)[[1]] - ctr) * k + dest, crs = 4326)

p <- ggplot() +
  geom_sf(data = grid, aes(fill = I(fill)), colour = "#0B1F3A", linewidth = 0.08) +
  geom_sf(data = india, fill = NA, colour = "#E8F1FA", linewidth = 0.18) +
  geom_segment(
    data = sun_rays, aes(x, y, xend = xend, yend = yend),
    colour = "#F6C453", linewidth = 0.55, lineend = "round"
  ) +
  geom_polygon(data = sun_body, aes(x, y), fill = "#F6C453") +
  geom_sf(data = cloud, fill = "#E8F1FA", colour = "#0B1F3A", linewidth = 0.35) +
  geom_polygon(data = drops, aes(x, y, group = id), fill = "#4FB3D9") +
  geom_path(
    data = wind, aes(x, y, group = id), colour = "#CFE3F5",
    linewidth = 0.55, lineend = "round"
  ) +
  coord_sf(xlim = c(67.5, 98), ylim = c(6.2, 37.8), expand = FALSE, datum = NA) +
  theme_void() +
  theme_transparent()

sticker(
  p,
  package = "varunayan",
  p_family = "albert-sans", p_fontface = "bold", p_size = 21,
  p_color = "#E8F1FA", p_y = 0.44,
  s_x = 1, s_y = 1.12, s_width = 1.12, s_height = 1.12,
  h_fill = "#0B1F3A", h_color = "#4FB3D9", h_size = 1.4,
  dpi = 600,
  filename = "R/man/figures/logo.png"
)

# hexSticker centres the hex unevenly; trim and pad equally
logo <- magick::image_trim(magick::image_read("R/man/figures/logo.png"))
logo <- magick::image_border(logo, "transparent", "12x12")
magick::image_write(logo, "R/man/figures/logo.png")

for (path in c(
  "R/pkgdown/varunayan_logo.png",
  "python/docs/assets/varunayan.png",
  "python/docs/_static/varunayan_logo.png",
  "python/docs/site_root/logo.png"
)) {
  magick::image_write(logo, path)
}

# Square icons: the hex centred on a transparent square.
square <- function(size) {
  info <- magick::image_info(logo)
  side <- max(info$width, info$height)
  sq <- magick::image_extent(logo, sprintf("%dx%d", side, side), gravity = "center", color = "none")
  magick::image_resize(sq, sprintf("%dx%d", size, size))
}
ico <- magick::image_join(square(16), square(32), square(48))
for (path in c("python/docs/_static/favicon.ico", "python/docs/site_root/favicon.ico", "R/pkgdown/favicon/favicon.ico")) {
  magick::image_write(ico, path, format = "ico")
}
fav <- "R/pkgdown/favicon"
magick::image_write(square(96), file.path(fav, "favicon-96x96.png"))
magick::image_write(square(192), file.path(fav, "web-app-manifest-192x192.png"))
magick::image_write(square(512), file.path(fav, "web-app-manifest-512x512.png"))
magick::image_write(magick::image_background(square(180), "white"), file.path(fav, "apple-touch-icon.png"))
png64 <- base64enc::base64encode(magick::image_write(square(256), format = "png"))
writeLines(sprintf(
  '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 256 256"><image width="256" height="256" xlink:href="data:image/png;base64,%s"/></svg>',
  png64
), file.path(fav, "favicon.svg"))

# Social preview cards (1200 x 630): the hex on the hex background colour.
card <- magick::image_blank(1200, 630, "#0B1F3A")
card <- magick::image_composite(card, magick::image_resize(logo, "x540"), gravity = "center")
magick::image_write(card, "python/docs/_static/varunayan_og.png")
magick::image_write(card, "R/man/figures/og-card.png")
