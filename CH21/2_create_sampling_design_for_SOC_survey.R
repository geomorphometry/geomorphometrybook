################################################################################
## Title: Create sampling designs for SOC mapping -----
## Description: Create sampling design for model calibration using covariate ,
##              space coverage sampling, and for model validation using a 
##              stratified random sampling for Ponui Island.  
## Date: 26.01.2025
## Author: M. Nussbaum, Utrecht University, Department of Physical Geography 
## Licence: CC-BY 4.0
################################################################################


library(terra)
library(fields)
library(sf)


# 1) Raster selection ---- 

# Prepare list of selected land surface parameter raster used either 
#  for data simulation or sampling design 
l.rast <- paste0("data/terrain/landsurf_param/", 
                 c("ponui_20m_nowater.tif", "ponui_20m_dsm_dem_diff.tif", "slope50m.tif", "tpi_450m.tif"))

r.dem20 <- rast(l.rast[1])
r.diff <- rast(l.rast[2])


# 2) Create SOC map to sample from ------

# Normally, this step would consist of actual sampling in the field and bringing 
# bags of soil into the laboratory for analysis, which would be done after section 3 and 4 of this code. 
# Here we add it before, so we can easily append the simulated topsoil SOC data to the sampling points.

# Use existing overview map as basis.  
# Dataset: Smap Predicted Carbon August 2022, Landcare Research
# Source: https://lris.scinfo.org.nz/layer/110217-smap-predicted-carbon-august-2022/
r.soc <- rast("data/soil/Smap Predicted Carbon August 2022.tif")
# transfer to 20 m resolution 
r.soc20 <- resample(r.soc, r.dem20)

# SOC maps were crated with gradient boosted trees algorithm. Distribution of SOC across 
# Ponui Island does not show large variability, likely regression tree based algorithms 
# tend to smooth the predicted distribution, somewhat extremer values (small or large) 
# are often not predicted. 
# Thus, we stretch values, as surrounding islands have ~9 % SOC in topsoil (according soil profiles from data viewer)
# scaling formula: y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
summary(r.soc)
values(r.soc20) <- 0.3 + (10 - 0.3) * (values(r.soc20) - 2.255) / (5.613 - 2.255)

# In addition, assume slight elevation trend
values(r.soc20) <-  values(r.soc20) + values(r.dem20)*0.014

# Also, assume larger values in in forests
r.diff[ values(r.diff) > 20 ] <- 20 # but not beyond tree height of 20 m
values(r.soc20) <-  values(r.soc20) + values(r.diff)*0.11

# Due to 100 m pixel resolution of overview map, 
# Ad-hoc fill in missing values with a step-wise nearest mean approach
r.soc20 <- focal(r.soc20, w = 5, na.policy = "only", fun = mean)
r.soc20 <- focal(r.soc20, w = 9, na.policy = "only", fun = mean)
r.soc20 <- focal(r.soc20, w = 25, na.policy = "only", fun = mean)
# also smooth the 100 m pixels somewhat
r.soc20 <- focal(r.soc20, w = 5, fun = mean, na.rm = T)
# remove water surface (set to NA in DEM in script 1)
r.soc20[ is.na(r.dem20) ] <- NA
names(r.soc20) <- "topsoil_soc"


# 3) Covariate space coverage sampling design for model training -------

# create a data frame with all pixels 
d.soc <- as.data.frame(r.soc20, xy = T, na.rm = F)
d.pixels <- cbind(d.soc, as.data.frame(rast(l.rast), xy = F, na.rm = F))

# scale numeric data
d.pixels <- d.pixels[ complete.cases(d.pixels), ]
rownames(d.pixels) <- 1:nrow(d.pixels)
d.pixels.scaled <- data.frame(scale(d.pixels))

# rounding, do because of possible convergence problems (see kmeans help page)
d.pixels.scaled <- round(d.pixels.scaled, 5)

# k-means clustering using 150 cluster centers = 150 samples 
set.seed(1)
l.sel <- c("ponui_20m_nowater", "slope50m", "tpi_450m")
m.kmeans <- kmeans(d.pixels.scaled[, l.sel], centers = 150, iter.max = 50)

# extract real points closest to cluster center
m.dist <- rdist(d.pixels.scaled[, l.sel], m.kmeans$centers)
# select index of this pixel
idx <- apply(m.dist, 2, which.min)

# create spatial point vectors from sampling points 
v.sample <- st_as_sf(d.pixels[idx, 1:3], coords = c("x", "y"), crs = 2193)
write_sf(v.sample, "results/sampling/cscs_design_150_SOC.gpkg")


# crate a map with the zones belonging to each sampling point 
# surveyors can use it to move the sampling point in case a location is not accessible 

# predict cluster for each pixel 
d.pixels$clusters <- fitted(m.kmeans, "classes")
# create raster from dataframe
r.clusters <- rast(d.pixels[, c("x", "y", "clusters")], type="xyz", crs= "epsg:2193")
# smooth for better visibility 
r.clusters.s <- focal(r.clusters, w = 3, fun = "modal")
writeRaster(r.clusters.s, filename = "results/sampling/cscs_design_150_cluster_areas.tif")



# 4) Stratified random sample for model validation ----

# use elevation for stratification, form 3 strata of equal size
t.breaks <- quantile(d.pixels$ponui_20m_nowater, probs = seq(0,1,1/3))
t.strata <- cut(d.pixels$ponui_20m_nowater, breaks = t.breaks, labels = 1:3)

set.seed(1)

# number of samples per stratum
n.stratum <- 10
# sample each stratum n times, apply to levels of cut function
idx <- c( sapply(levels(t.strata), function(stratum){
  # select relevant pixel indices 
  sel <- (1:nrow(d.pixels))[ t.strata == stratum ]
  # random sample from selected pixels with simple sample() function 
  idx <- sel[ sample(1:length(sel), n.stratum) ]
  return(idx)
}) )

# create spatial point vectors from sampling points 
v.validation <- st_as_sf(d.pixels[idx, 1:3], coords = c("x", "y"), crs = 2193)
write_sf(v.validation, "results/sampling/strs_design_30_SOC.gpkg")

# create a map with the strata
t.breaks[1] <- 0
r.strata <- classify(r.dem20, rcl = t.breaks)
writeRaster(r.strata, filename = "results/sampling/strs_design_3elevation_strata.tif")
