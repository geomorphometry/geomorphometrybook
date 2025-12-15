################################################################################
## Title: Derive land surface parameters from DEM -----
## Description: Calculate a wide range of land surface parameters for soil mapping,
##              use different resolution to obtain multi-scale representation of
##              processes (e.g. erosion, accumulation), target resolution 20 m
##              for Ponui Island. 
##              SAGA GIS needs to be installed for use in the background. 
## Date: 26.01.2025
## Author: M. Nussbaum, Utrecht University, Department of Physical Geography 
## Licence: CC-BY 4.0
################################################################################

# NOTE Variable naming convention: d.: data.frames, v.:spatial vector geometries, 
# r.: spatial raster, l.: character vector used as list or a list(), 
# t.: numeric vector, m: matrix 

# Folder structure:
#  data : original and processed model input data
#  data/landmask : downloaded Ponui Island outline
#  data/soil : downloaded overview SOC map
#  data/surface : downloaded digital surface model
#  data/terrain/ : downloaded digital elevation model
#  data/terrain/landsurf_param : derived land surface parameters
#  results/ : 
#  results/mapping : resulting spatial prediction maps (script 3)
#  results/sampling : resulting sampling designs (script 2)


# load relevant packages 
library(sf)
library(terra)
library(Rsagacmd)

# TODO remove
setwd("~/cloud-uu/3_paper_div/2024_geomorphometry/examples_ponui/code_cleaned_for_sharing/")

# Setup bridge to SAGA
saga <- saga_gis(raster_backend = "terra", vector_backend = "sf")

## 1) Prepare elevation model -----

# attach elevation model (1 m resolution)
r.dem1 <- rast("data/terrain/ponui_island_dtm.tif")

# Create a 20 m elevation model of only the land surface 
#   Water is labeled NA. 
#   By removing all NA pixels, it will serve as mask to create the soil map in script 3

# Create land mask 
# downloaded Ponui Island polygon from: Statistical Area 2 2023 (generalised), Stats NZ 
# https://datafinder.stats.govt.nz/layer/111227-statistical-area-2-2023-generalised/
v.island <- st_read("data/landmask/statistical-area-2-2023-generalised.gpkg")
# add buffer to truly cover all
v.island.buf <- st_buffer(v.island, dist = 100)
# transform to raster
r.island.buf <- rasterize(v.island.buf, r.dem1)

# set everything outside the raster maks to NA
r.dem1nw <- r.dem1
r.dem1nw[ is.na(r.island.buf) ] <- NA
# if there are still pixels below sea level, assume them to be water 
r.dem1nw[ values(r.dem1nw) < 0 ] <- NA
# aggregate to 20 m pixels 
r.dem20nw <- aggregate(r.dem1nw, 20)
writeRaster(r.dem20nw, filename ="data/terrain/landsurf_param/ponui_20m_nowater.tif")  


# aggregate to 20 m and 50 m pixels 
#  (including water areas to reduce NA in subsequent calculations) 
r.dem20 <- aggregate(r.dem1, 20)
r.dem50 <- aggregate(r.dem1, 50)


# 2) Basic land surface parameters: slope, aspect, curvatures ------

## at 20 m resolution 
l.morph20 <- saga$ta_morphometry$slope_aspect_curvature(elevation = r.dem20, unit_slope = "percent")
# transform aspect into 2 indices, northness and eastness 
l.morph20$aspect_eness <- sin(l.morph20$aspect) 
l.morph20$aspect_nness <- cos(l.morph20$aspect) 
# write the relevant ones to file, use apply function (similar to for loop)
l.sel <- c("slope", "aspect_eness", "aspect_nness", "c_gene", "c_prof", "c_plan") # selection
lapply(l.sel, function(rast.name){
  writeRaster(l.morph20[[rast.name]], filename = paste0("data/terrain/landsurf_param/", rast.name,"20m.tif"))  
})

## derive at 50 m resolution and resample to 20 m 
l.morph50 <- saga$ta_morphometry$slope_aspect_curvature(elevation = r.dem50, unit_slope = "percent")
# transform aspect into 2 indices, northness and eastness 
l.morph50$aspect_eness <- sin(l.morph50$aspect) 
l.morph50$aspect_nness <- cos(l.morph50$aspect) 
# write the relevant ones to file, use apply function (similar to for loop)
lapply(l.sel, function(rast.name){
  r.tmp <- resample(l.morph50[[rast.name]], r.dem20)
  gf <- focalMat(r.tmp, 9, "Gauss")
  focal(r.tmp, w = gf, fun = mean, na.rm = T, filename = paste0("data/terrain/landsurf_param/", rast.name,"50m.tif"))
})



# 3) Upslope + downslope curvature  ------

## at 20 m resolution 
l.cup20 <- saga$ta_morphometry$upslope_and_downslope_curvature(dem = r.dem20)
writeRaster(l.cup20$c_up, filename = "data/terrain/landsurf_param/curvup20m.tif")
writeRaster(l.cup20$c_down, filename = "data/terrain/landsurf_param/curvdown20m.tif")

## derive at 50 m resolution and resample to 20 m 
l.cup50 <- saga$ta_morphometry$upslope_and_downslope_curvature(dem = r.dem50)
r.cup50 <- resample(l.cup50$c_up, r.dem20)
r.cdown50 <- resample(l.cup50$c_down, r.dem20)
# smoothing to remove 50 m pixel artefacts after resampling 
gf <- focalMat(r.cup50, 9, "Gauss")
focal(r.cup50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/curvup50m.tif")
focal(r.cdown50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/curvdown50m.tif")


# 4) Various morphometric indices ------

# Morphometric Protection Index (MPI)

## at 20 m resolution 
r.mpi20 <- saga$ta_morphometry$morphometric_protection_index(dem = r.dem20, radius = 150)
# The search radius of the MPI causes some NA in the outer part of the island 
# normally, it would be recommended to use a larger DEM. Here we do some ad-hoc filling in of the 
# missing data by computing a step-wise local mean and assigning that to NA pixels
r.mpi20.s <- focal(r.mpi20, w = 7, fun = mean, na.policy = "only")
focal(r.mpi20.s, w = 9, fun = mean, na.policy = "only", filename = "data/terrain/landsurf_param/mpi20m.tif")

## derive at 50 m resolution and resample to 20 m 
r.mpi50 <- saga$ta_morphometry$morphometric_protection_index(dem = r.dem50, radius = 150)
r.mpi50 <- resample(r.mpi50, r.dem20)
# smoothing to remove 50 m pixel artefacts after resampling 
# first do some NA filling
r.mpi50.s <- focal(r.mpi50, w = 9, fun = mean, na.policy = "only")
r.mpi50.s <- focal(r.mpi50.s, w = 9, fun = mean, na.policy = "only")
gf <- focalMat(r.mpi50.s, 9, "Gauss")
focal(r.mpi50.s, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/mpi50m.tif")


# Vector Ruggedness Measure (VRM)

## at 20 m resolution 
r.vrm20 <- saga$ta_morphometry$vector_ruggedness_measure_vrm(dem = r.dem20, radius = 5)
writeRaster(r.vrm20, filename = "data/terrain/landsurf_param/vrm20m.tif")

## derive at 50 m resolution and resample to 20 m 
r.vrm50 <- saga$ta_morphometry$vector_ruggedness_measure_vrm(dem = r.dem50, radius = 5)
r.vrm50 <- resample(r.vrm50, r.dem20)
# smoothing to remove 50 m pixel artefacts after resampling 
gf <- focalMat(r.vrm50, 9, "Gauss")
focal(r.vrm50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/vrm50m.tif")


# Terrain Ruggedness Index (TRI)

## at 20 m resolution 
r.tri20 <- saga$ta_morphometry$terrain_ruggedness_index_tri(dem = r.dem20, radius = 5)
writeRaster(r.tri20, filename = "data/terrain/landsurf_param/tri20m.tif")

## derive at 50 m resolution and resample to 20 m 
r.tri50 <- saga$ta_morphometry$terrain_ruggedness_index_tri(dem = r.dem50, radius = 5)
r.tri50 <- resample(r.tri50, r.dem20)
# smoothing to remove 50 m pixel artefacts after resampling 
gf <- focalMat(r.tri50, 9, "Gauss")
focal(r.tri50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/tri50m.tif")


# Relative Heights and Slope Positions

## at 20 m resolution 
l.rels20 <- saga$ta_morphometry$relative_heights_and_slope_positions(dem = r.dem20)
# write the relevant ones to file, use apply function (similar to for loop)
lapply(names(l.rels20), function(rast.name){
  writeRaster(l.rels20[[rast.name]], filename = paste0("data/terrain/landsurf_param/relpos_", rast.name,"20m.tif"))  
})

## derive at 50 m resolution and resample to 20 m 
l.rels50 <- saga$ta_morphometry$relative_heights_and_slope_positions(dem = r.dem50)
# write the relevant ones to file, use apply function (similar to for loop)
lapply(names(l.rels20), function(rast.name){
  r.tmp <- resample(l.rels50[[rast.name]], r.dem20)
  gf <- focalMat(r.tmp, 9, "Gauss")
  focal(r.tmp, w = gf, fun = mean, na.rm = T, filename = paste0("data/terrain/landsurf_param/relpos_", rast.name,"50m.tif"))
})




## 5) Topographic wetness index ------

## at 20 m resolution 
l.twi20 <- saga$ta_hydrology$saga_wetness_index( dem = r.dem20)
writeRaster(l.twi20$twi, filename = "data/terrain/landsurf_param/twi20m.tif")
# log transform of skewed catchment area with slight comma shift
l.twi20$area_mod <- log(l.twi20$area_mod + 0.01)
writeRaster(l.twi20$area_mod, filename = "data/terrain/landsurf_param/twi_areamodlog20m.tif")

## derive at 50 m resolution and resample to 20 m 
l.twi50 <- saga$ta_hydrology$saga_wetness_index( dem = r.dem50)
r.twi50 <- resample(l.twi50$twi, r.dem20)
r.areamod50 <- resample(l.twi50$area_mod, r.dem20)
r.areamod50 <- log(r.areamod50 + 0.01)
# smoothing to remove 50 m pixel artefacts after resampling 
gf <- focalMat(r.twi50, 9, "Gauss")
focal(r.twi50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/twi50m.tif")
focal(r.areamod50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/twi_areamodlog50m.tif")

# large scale TWI, apply strong smoothing 
gf <- focalMat(r.twi50, 100, "Gauss")
r.twi50.s <- focal(r.twi50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/twi50m_s100.tif")



# 6) Multiresolution Index of Valley Bottom Flatness (MRVBF) ------

## at 20 m resolution 
l.mrvbf20 <- saga$ta_morphometry$multiresolution_index_of_valley_bottom_flatness_mrvbf(dem = r.dem20)
writeRaster(l.mrvbf20$mrvbf, filename = "data/terrain/landsurf_param/mrvbf20m.tif")
writeRaster(l.mrvbf20$mrrtf, filename = "data/terrain/landsurf_param/mrrtf20m.tif")

## derive at 50 m resolution and resample to 20 m 
l.mrvbf50 <- saga$ta_morphometry$multiresolution_index_of_valley_bottom_flatness_mrvbf(dem = r.dem50)
r.mrvbf50 <- resample(l.mrvbf50$mrvbf, r.dem20)
r.mrrtf50 <- resample(l.mrvbf50$mrrtf, r.dem20)
# smoothing to remove 50 m pixel artefacts after resampling 
gf <- focalMat(r.mrvbf50, 9, "Gauss")
focal(r.mrvbf50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/mrvbf50m.tif")
focal(r.mrrtf50, w = gf, fun = mean, na.rm = T, filename = "data/terrain/landsurf_param/mrrtf50m.tif")



# 7) Topographic Position Indices ------
#     Use different side length of rectangular window for focal mean operation 

f <- matrix(1, nrow=5, ncol=5)
tt <- ceiling(sum(f)/2) # determine center pixel
focal(r.dem20, w = f, fun = function(x, ...){ x[tt] - mean(x[-tt], na.rm = T) }, 
      filename = "data/terrain/landsurf_param/tpi_100m.tif")

f <- matrix(1, nrow=9, ncol=9)
tt <- ceiling(sum(f)/2)
focal(r.dem20, w = f, fun = function(x, ...){ x[tt] - mean(x[-tt], na.rm = T) }, 
      filename = "data/terrain/landsurf_param/tpi_180m.tif")

f <- matrix(1, nrow=17, ncol=17)
tt <- ceiling(sum(f)/2)
focal(r.dem20, w = f, fun = function(x, ...){ x[tt] - mean(x[-tt], na.rm = T) }, 
      filename = "data/terrain/landsurf_param/tpi_340m.tif")

# use 50 m DEM to speed up calculation for large radii
f <- matrix(1, nrow=9, ncol=9)
tt <- ceiling(sum(f)/2)
r.tpi <- focal(r.dem50, w = f, fun = function(x, ...){ x[tt] - mean(x[-tt], na.rm = T) })
resample(r.tpi, r.dem20, filename = "data/terrain/landsurf_param/tpi_450m.tif")

f <- matrix(1, nrow=15, ncol=15)
tt <- ceiling(sum(f)/2)
r.tpi <- focal(r.dem50, w = f, fun = function(x, ...){ x[tt] - mean(x[-tt], na.rm = T) })
resample(r.tpi, r.dem20, filename = "data/terrain/landsurf_param/tpi_750m.tif")



# 8) Vegetation height (DEM vs. DSM difference)  -----

r.dsm1 <- rast("data/surface/ponui_island_dsm.tif")
# compareGeom(r.dem1, r.dsm1); origin(r.dem1); origin(r.dsm1) 
# extent and origin does not match, due to origin mismatch, resampling is needed, not just cropping
r.dsm1 <- resample(r.dsm1, r.dem1)
# difference at 1 m pixel level
r.diff <- r.dsm1 - r.dem1
# transform to 20 m
r.diff20 <- resample(r.diff, r.dem20)
# assume negative vegetation heights are errors and set to zero
r.diff20[ values(r.diff20) < 0 ] <- 0
r.diff20 <- focal(r.diff20, w = 5, na.policy = "only", fun = mean, filename = "data/terrain/landsurf_param/ponui_20m_dsm_dem_diff.tif")



# 9) Check raster file consistency ----

# create a list of land surface parameter raster files 
l.f <- list.files("data/terrain/landsurf_param/", pattern = "\\.tif$", full.names = T)

# check for difference in extent, resolution or CRS 
# t.issue <- sapply(l.f, function(rast.path){ compareGeom(r.dem20, rast(rast.path), res = T, stopOnError = F) } )
# list rasters with issues
# l.f[!t.issue]

# Fix raster object naming (ensures transfer to dataframe with correct col names)
# all rasters saved after e.g. focal operations have object name "focal_mean" which results in duplicate col names. 
sapply(l.f, function(rast.path){ 
  # check if raster object name corresponds to file name
  file.name <- gsub("\\.tif$", "", basename(rast.path))
  if( names(rast(rast.path)) != file.name ){
    # if it does not match, assign new name to raster object 
    # first rename existing file (to retain name for new raster)
    name.old <- gsub("\\.tif$", "-old.tif", rast.path)
    file.rename(rast.path, name.old)
    r.tmp <- rast(name.old)
    names(r.tmp) <- file.name 
        writeRaster(r.tmp, rast.path)
    file.remove(name.old)
    cat("Fixed ", rast.path, "\n")
  } 
})
