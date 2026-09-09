## ---------------------------
##
## Script name: geomorphometry_geostatistical_simulation.R
##
## Purpose of script: Geostatistical simulation of DEM errors and their impact on terrain analysis (TPI) for Chapter 5.
##
## Output: Simulated DEM errors and TPI maps
##
## Author: Dr. Laurence Hawker
##
## Date Created: 2026-01-12
##
## Copyright (c) Laurence Hawker, 2026
## Email: laurence.hawker.bristol.ac.uk
##
## ---------------------------
##
## Notes:
##   
##
## ---------------------------

library(terra)
library(gstat)
library(sf)
library(dplyr)
library(tidyr)
library(ggplot2)
library(tidyterra)
library(ggpubr)
library(scico)

# Load Ponhui DEM
data_dir <- 'Path to Data' # <-- CHANGE THIS TO YOUR DATA DIRECTORY
fig_dir <- 'Path to Figures' # <-- CHANGE THIS TO YOUR FIGURE DIRECTORY

lidar_path <- file.path(data_dir,'ponui_island_dtm.tif')
extent_path <- file.path(data_dir, 'ponui_extent.gpkg')
fabdem_path <- file.path(data_dir, 'S37E175_FABDEM_V1-2.tif')

# Ponui dtm from LiDAR as a raster
lidar_1m <- rast(lidar_path) 

# Cropping Polygon to extent of Ponui Island
ponui_crop <- st_read(extent_path)

# Reproject crop geometry if needed
ponui_crop <- st_transform(ponui_crop, crs(lidar_1m))

# Crop LiDAR to extent of Ponui Island
lidar_crop <- crop(lidar_1m, vect(ponui_crop))

# Load FABDEM
fabdem <- rast(fabdem_path)

# Reproject FABDEM to NZ coordinate system
fabdem_nz <- project(fabdem, crs(lidar_crop), method = "bilinear")

# Crop to Ponui extent
fabdem_crop <- crop(fabdem_nz, vect(ponui_crop))

# Sample elevation points from LiDAR
set.seed(42)

# Sample points
n_points <- 200
pts <- spatSample(
  lidar_crop,
  size = n_points,
  method = "random",
  as.points = TRUE,
  values = TRUE
)

names(pts) <- "height"

## Derive DEM Errors as the difference between FABDEM and LiDAR elevation
pts$fabdem <- terra::extract(fabdem_crop, pts)[,2]
pts$error  <- pts$fabdem - pts$height

pts_sf <- st_as_sf(pts) |>
  filter(!is.na(error)) |>
  distinct(geometry, .keep_all = TRUE)


# Prepare covariates: slope and insolation
slope <- terrain(fabdem_crop, v = "slope", unit = "radians")
solin <- cos(slope)

pts_sf$slope <- terra::extract(slope, pts_sf)[,2]
pts_sf$solin <- terra::extract(solin, pts_sf)[,2]

pts_sf <- pts_sf |>
  filter(!is.na(slope), !is.na(solin))

## Variogram of DEM errors
v_err <- variogram(error ~ 1, pts_sf)
vgm_err <- fit.variogram(v_err, vgm("Exp"))

v_err_cov <- variogram(error ~ slope + solin, pts_sf)
vgm_err_cov <- fit.variogram(v_err_cov, vgm("Exp"))

# conert to dataframes
v_plain_df <- as.data.frame(v_err)
v_cov_df   <- as.data.frame(v_err_cov)

v_plain_df$type <- "No covariates"
v_cov_df$type   <- "With slope + solin"

v_err_df <- rbind(v_plain_df, v_cov_df)


## Conditional Simulation

# --- Simulation grid (modern sf version) ---

fabdem_vect <- as.points(fabdem_crop)

sim_grid <- st_as_sf(fabdem_vect)

# Add terrain covariates
sim_grid$slope <- terra::extract(slope, sim_grid)[,2]
sim_grid$solin <- terra::extract(solin, sim_grid)[,2]

## Conditional simulation of DEM errors

nsim = 100 #number of simulations

err_sim_plain <- krige(
  error ~ 1,
  locations = pts_sf,
  newdata = sim_grid,
  model = vgm_err,
  nsim = nsim,
  nmax = 50
)

err_sim_cov <- krige(
  error ~ slope + solin,
  locations = pts_sf,
  newdata = sim_grid,
  model = vgm_err_cov,
  nsim = nsim,
  nmax = 50
)

# Extract simulation columns only
sim_mat_plain <- as.matrix(err_sim_plain[, paste0("sim", 1:nsim)])
sim_mat_cov   <- as.matrix(err_sim_cov[, paste0("sim", 1:nsim)])

# Create a template raster
template <- fabdem_crop

# Convert to a raster stack

# Create empty raster stack
err_rasters_plain <- rast(template, nlyr = nsim)
err_rasters_cov   <- rast(template, nlyr = nsim)

# write values into each layer (probably a better way to do this)
for(i in 1:nsim) {
  
  v_plain <- as.numeric(unlist(sim_mat_plain[, i]))
  v_cov   <- as.numeric(unlist(sim_mat_cov[, i]))
  
  values(err_rasters_plain[[i]]) <- v_plain
  values(err_rasters_cov[[i]])   <- v_cov
}

# Calculate mean surafaces
err_mean_plain <- mean(err_rasters_plain)
err_mean_cov   <- mean(err_rasters_cov)
err_mean_cov20   <- mean(err_rasters_cov[[1:20]])

# Calculate TPI (TWI not available in terra)
tpi_single <- terrain(fabdem_crop + err_rasters_cov[[1]], v = "TPI")
tpi_mean   <- terrain(fabdem_crop + err_mean_cov, v = "TPI")
tpi_mean20   <- terrain(fabdem_crop + err_mean_cov20, v = "TPI")

## Plot Figure 5.15 — TWI from single vs mean of 100 simulations (2 columns)

# calculate TPI range for plots
tpi_rng <- range(
  c(values(tpi_single), values(tpi_mean), values(tpi_mean20)),
  na.rm = TRUE
)

p5_15a <- ggplot() +
  geom_spatraster(data = tpi_single) +
  scale_fill_scico(palette = "batlow", limits = tpi_rng, na.value = "transparent") +
  labs(title = "TPI: single realisation",
       fill = "TPI") +
  theme_minimal()+
  theme(legend.position = "none")

p5_15b <- ggplot() +
  geom_spatraster(data = tpi_mean20) +
  scale_fill_scico(palette = "batlow", limits = tpi_rng, na.value = "transparent") +
  labs(title = "TPI: mean of 20 realisations",
       fill = "TPI") +
  theme_minimal()+
  theme(legend.position = "none")

p5_15c <- ggplot() +
  geom_spatraster(data = tpi_mean) +
  scale_fill_scico(palette = "batlow", limits = tpi_rng, na.value = "transparent") +
  labs(title = "TPI: mean of 100 realisations",
       fill = "TPI") +
  theme_minimal()+
  theme(legend.position = "none")

# Arrange
fig5_15 <- (p5_15a + p5_15b + p5_15c) +
  plot_layout(ncol = 3, guides = "collect") +
  plot_annotation(tag_levels = "a",tag_prefix = "(",tag_suffix = ")") &
  theme(
    legend.position = "bottom",
    legend.key.width = unit(1.5, "cm"),
    legend.title = element_text(size = 10),
    legend.text = element_text(size = 9)
  )

fig5_15


## Figure 5.17 — Smooth vs noisy surfaces (ANUDEM vs geostatistical simulation)


# One simulated DEM realisation (FABDEM + one error realisation)
dem_sim <- fabdem_crop + err_rasters_cov[[1]]


# Calculate elevation ranges for the shared legend
elev_rng <- range(
  c(values(fabdem_crop), values(dem_sim)),
  na.rm = TRUE
)

# Make plots
p5_17a <- ggplot() +
  geom_spatraster(data = fabdem_crop) +
  scale_fill_scico(
    palette = "fes",
    begin = 0.5,
    limits = elev_rng,        # <-- IMPORTANT
    na.value = "transparent"
  ) +
  labs(title = "Deterministic surface (FABDEM)",
       fill = "Elevation (m)") +
  theme_minimal() +
  theme(legend.position = "none")

p5_17b <- ggplot() +
  geom_spatraster(data = dem_sim) +
  scale_fill_scico(
    palette = "fes",
    begin = 0.5,
    limits = elev_rng,        # <-- IMPORTANT
    na.value = "transparent"
  ) +
  labs(title = "Conditional geostatistical simulation",
       fill = "Elevation (m)") +
  theme_minimal() +
  theme(legend.position = "none")

# Combine figures
fig5_17 <- (p5_17a + p5_17b) +
  plot_layout(ncol = 2, guides = "collect") +
  plot_annotation(tag_levels = "a",tag_prefix = "(",tag_suffix = ")") &   
  theme(
    legend.position = "bottom",
    legend.key.width = unit(1.5, "cm"),
    legend.title = element_text(size = 10),
    legend.text = element_text(size = 9)
  )

fig5_17



## Figure 5.18 — Error modelling: variogram + histogram + simulated errors (2×2 layout)

# Common colour range for error maps
err_rng <- range(
  c(values(err_mean_plain), values(err_mean_cov)),
  na.rm = TRUE
)

# Histogram stats
err_vals <- pts_sf$error
err_vals <- err_vals[!is.na(err_vals)]

err_mean <- mean(err_vals)
err_sd   <- sd(err_vals)

err_hist_df <- data.frame(error = err_vals)


# Empirical vs fitted variogram

# Create model lines as data frames
vline_plain <- as.data.frame(
  variogramLine(vgm_err, maxdist = max(v_err$dist))
) |>
  mutate(model = "No covariates")

vline_cov <- as.data.frame(
  variogramLine(vgm_err_cov, maxdist = max(v_err_cov$dist))
) |>
  mutate(model = "With slope + solin")

# Bind them together for tidy plotting
vline_df <- rbind(vline_plain, vline_cov)

# Plot
vplot <- ggplot() +
  # empirical variogram points (no colour distinction)
  geom_point(
    data = as.data.frame(v_err),
    aes(x = dist, y = gamma),
    size = 2,
    alpha = 0.6
  ) +
  # fitted variogram models with DIFFERENT LINETYPES
  geom_line(
    data = vline_df,
    aes(x = dist, y = gamma, linetype = model),
    linewidth = 1
  ) +
  scale_linetype_manual(
    values = c("solid", "dashed")
  ) +
  labs(
    title = "Variogram of elevation errors",
    x = "Distance (m)",
    y = "Semivariance",
    linetype = "Model"
  ) +
  theme_minimal() +
  theme(
    legend.position = "bottom"
  )

vplot


# Histogram of errors
hplot <- ggplot(err_hist_df, aes(x = error)) +
  geom_histogram(bins = 40, fill = "grey60", colour = "black") +
  geom_vline(xintercept = err_mean, linetype = "dashed", linewidth = 0.8) +
  annotate(
    "text",
    x = max(err_vals, na.rm = TRUE) * 0.6,
    y = Inf,
    vjust = 2,
    label = sprintf("Mean = %.2f m\nSD = %.2f m", err_mean, err_sd),
    hjust = 0
  ) +
  labs(
    title = "Histogram of elevation errors",
    x = "Error (m)",
    y = "Frequency"
  ) +
  theme_minimal()


# Simulated Errors (no covariates)
p5_18c <- ggplot() +
  geom_spatraster(data = err_mean_plain) +
  scale_fill_scico(palette = "vikO",limits=err_rng, na.value = "transparent") +
  labs(title = "Simulated errors (no covariates)",
       fill = "Error (m)") +
  theme_minimal() +
  theme(legend.position = 'none')

# Simulated errors (with slope and insolation)
p5_18d <- ggplot() +
  geom_spatraster(data = err_mean_cov) +
  scale_fill_scico(palette = "vikO", limits = err_rng, na.value = "transparent") +
  labs(title = "Simulated errors (slope + solin)",
       fill = "Error (m)") +
  theme_minimal()+
  theme(legend.position = 'none')

# Plot as 1 figure
top_row <- vplot + hplot

bottom_row <- (p5_18c + p5_18d) +
  plot_layout(guides = "collect")

fig5_18 <- (top_row / bottom_row) +
  plot_annotation(tag_levels = "a",tag_prefix = "(",tag_suffix = ")") &
  theme(
    legend.position = "bottom",
    legend.key.width = unit(1.5, "cm"),
    legend.title = element_text(size = 10),
    legend.text = element_text(size = 9)
  )

fig5_18


## Figure 5.19 — TWI from simulated points vs simulated DEM (2 columns)

# Single realization from simulated points
tpi_points_single <- terrain(fabdem_crop + err_rasters_cov[[1]], v = "TPI")

# Mean of 100 realisations
tpi_points_mean <- terrain(fabdem_crop + err_mean_cov, v = "TPI")


tpi2_rng <- twi_rng <- range(
  c(
    values(tpi_points_single),
    values(tpi_points_mean),
    values(tpi_single),
    values(tpi_mean)
  ),
  na.rm = TRUE
)


p5_19a <- ggplot() +
  geom_spatraster(data = tpi_points_single) +
  scale_fill_scico(palette = "batlow", limits = tpi2_rng, na.value = "transparent") +
  labs(title = "TPI: single simulated points",
       fill = "TPI") +
  theme_minimal() +
  theme(legend.position = "none")


p5_19b <- ggplot() +
  geom_spatraster(data = tpi_points_mean) +
  scale_fill_scico(palette = "batlow", limits = tpi2_rng, na.value = "transparent") +
  labs(title = "TPI: mean of 100 simulated points",
       fill = "TPI") +
  theme_minimal()+
  theme(legend.position = "none")

p5_19c <- ggplot() +
  geom_spatraster(data = tpi_single) +
  scale_fill_scico(palette = "batlow", limits = tpi2_rng, na.value = "transparent") +
  labs(title = "TPI: single simulated DEM",
       fill = "TPI") +
  theme_minimal() +
  theme(legend.position = "none")


p5_19d <- ggplot() +
  geom_spatraster(data = tpi_mean) +
  scale_fill_scico(palette = "batlow", limits = tpi2_rng, na.value = "transparent") +
  labs(title = "TPI: mean of 100 simulated DEM",
       fill = "TPI") +
  theme_minimal()+
  theme(legend.position = "none")


# Combine
fig5_19 <- ( (p5_19a + p5_19b) /
               (p5_19c + p5_19d) ) +
  plot_layout(guides = "collect") +
  plot_annotation(tag_levels = "a",tag_prefix = "(",tag_suffix = ")") &
  theme(
    legend.position = "bottom",
    legend.key.width = unit(1.5, "cm"),
    legend.title = element_text(size = 10),
    legend.text = element_text(size = 9)
  )

fig5_19



# Save all figures
ggsave(file.path(fig_dir,"fig5_15_twi_simulations.png"), fig5_15, width = 16, height = 7, dpi = 300)
ggsave(file.path(fig_dir,"fig5_17_surfaces.png"), fig5_17, width = 16, height = 7, dpi = 300)
ggsave(file.path(fig_dir,"fig5_18_errors.png"), fig5_18, width = 16, height = 12, dpi = 300)
ggsave(file.path(fig_dir,"fig5_19_twi_comparison.png"), fig5_19, width = 16, height = 7, dpi = 300)

