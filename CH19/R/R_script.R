# ==== Set Working Directory ====
setwd(here::here()) # Set working directory as location of .Rproj file

# ==== Load General Packages ====
library(dplyr)   # Data wrangling
library(ggplot2) # Plotting
library(sf)      # Spatial vector data
library(terra)   # Spatial raster data
library(tmap)    # Advanced spatial plotting

# ==== Set Up Color Palettes ====
hill_pal <- grey(0:100 / 100) # Hillshade color scale
cont_pal <- viridis::viridis(100) # Continuous color scale
div_pal <- colorRampPalette(c("blue", "gray", "red"))(101) # Diverging color scale
circle_pal <- cetcolor::cet_pal(100, "c2") # Circular color scale
feat_pal <- c("gray", "orange", "black", "blue", "green", "yellow", "red") # features color scale
flow_pal <- c(
  "0" = "#CCCCCC", # flat / no flow (neutral gray)
  "1" = "#E41A1C", # East
  "2" = "#FF7F00", # SE
  "4" = "#FFFF33", # S
  "8" = "#4DAF4A", # SW
  "16" = "#377EB8", # W
  "32" = "#984EA3", # NW
  "64" = "#A65628", # N
  "128" = "#000000" # NE
) # flow direction color scale

# ==== Spatial Data Handling ====
# Purpose: Read in data

# We can use read_sf() from the sf package to read in spatial vector data as a special
# type of data.frame with attached geometry and the rast() function of the terra package
# to read in spatial raster data

ponui_border <- read_sf("../Data/ponui_buffer10m.gpkg") # Read in island border vector file
ponui_dtm <- rast("../Data/ponui_island_dtm.tif") # Read in raster DTM

# These objects can be plotted using the plot() function
plot(ponui_dtm, main = "Ponui Island DTM", axes = FALSE, reset = FALSE) # Use reset = FALSE if adding additional layers
plot(st_geometry(ponui_border), border = "white", add = TRUE) # add = TRUE layers on top of current plot

# ==== Gridding LiDAR Point Clouds ====
# Purpose: Create a 1 m gridded DTM and explore point cloud metrics

# If we did not have a gridded DTM already, we could create one ourselves from the
# LiDAR point cloud using the lidR package
library(lidR) # For handling LiDAR data
# We can use the readLAS() function of the lidR package to read in a LiDAR point cloud.
# `select = "xyzc"` indicates to include the positioning information (xy), the elevation (z),
# and the classification (c), and `filter = "-keep_class 2"` indicates to only
# read in points that are of classification type 2 which corresponds to ground points.
ponui_las <- readLAS(
  "../Data/ponui.las",
  select = "xyzc",
  filter = "-keep_class 2"
) # Read in LiDAR data

# To speed up the example, we will crop this data to a smaller subregion
# (this step is not needed if you want to process the entire island)
cropped_ext <- ext(1794425.37, 1795350.27, 5918388.57, 5919313.48) # Create a smaller extent
ponui_dtm_cropped <- crop(ponui_dtm, cropped_ext) # Crop existing Ponui Island DTM

plot(ponui_dtm_cropped, main = "Existing Cropped DTM", axes = FALSE)
ponui_las <- clip_rectangle(
  ponui_las,
  xleft = cropped_ext[1],
  ybottom = cropped_ext[3],
  xright = cropped_ext[2],
  ytop = cropped_ext[4]
) # Crop lidar points

# We can examine our point cloud using a variety of functions, which can help inform
# a suitable resolution to form our grided data product.
npoints(ponui_las) # number of points
area(ponui_las)    # area (in m2)
density(ponui_las) # point density (poins/m2)

# Since the existing DTM we read in earlier (ponui_dtm) has a 1 m resolution, we
# will proceed to grid the LiDAR points to a 1 m resolution grid.

# We can calculate and visualize the point density and standard deviation of
# elevation values within each 1 m grid cell.
las_density_1m <- rasterize_density(ponui_las, res = 1) # calculate the point density per pixel in a 1m res raster
plot(
  las_density_1m,
  main = "Point Density 1m",
  range = c(1, unlist(global(las_density_1m, max, na.rm = TRUE))),
  axes = FALSE
)

las_sd_1m <- pixel_metrics(ponui_las, ~ sd(Z), res = 1) # calculate the standard deviation of values per pixel in a 1m res raster
plot(las_sd_1m, main = "Standard Deviation", axes = FALSE)

# Create a regularly gridded DTM using the tin algorithm which is based on Delaunay triangulation
lidR_dtm <- rasterize_terrain(ponui_las, res = 1, algorithm = tin()) # Create a regularly gridded DTM using the tin algorithm

# From this you can see our DTM we created from the LiDAR is very similar to the
# existing DTM we read in earlier
par(mfrow = c(1, 2)) # Put plots side by side
plot(ponui_dtm_cropped, main = "Existing Cropped DTM", axes = FALSE)
plot(lidR_dtm, main = "Our LiDAR DTM", axes = FALSE)
dev.off() # reset graphics

# ==== Deriving Land Surface Parameters ====
# Purpose: Derive land surface parameters (LSPs) using terra, MultiscaleDTM, and SurfRough

# We can calculate some land surface parameters (LSP) from within the terra package
# using the terrain() function
ponui_dtm_terra_params <- terrain(
  ponui_dtm_cropped,
  v = c(
    "slope",
    "aspect",
    "TPI",
    "TRI",
    "TRIriley",
    "TRIrmsd",
    "roughness",
    "flowdir"
  ),
  unit = "radians",
  neighbors = 8
)
# terra can also calculate hillshade via the shade() function which is useful for
# visualization of 3d structures.
# It can be plotted in gray scale and other maps overlain as a semi-transparent layer.
hillshade <- shade(
  slope = ponui_dtm_terra_params$slope,
  aspect = ponui_dtm_terra_params$aspect,
  angle = 45,
  direction = 315
)

# More advanced plotting can be accomplished with the tmap package which uses
# the `+` operator to systematically add elements to plots
hs <- tm_shape(hillshade) +
  tm_raster(
    col.scale = tm_scale_continuous(values = hill_pal),
    col.legend = tm_legend(show = FALSE)
  ) # Plot hillshade
hs # plot hillshade

# Overlay terra::terrain() results on hillshade using tmap
# Here `+` is used to add to plots, the scale is supplied per each layer,
# and `col.alpha` sets the transparency

hs +
  tm_shape(ponui_dtm_terra_params) +
  tm_raster(
    col = names(ponui_dtm_terra_params),
    col.scale = list(
      tm_scale_continuous(values = cont_pal),  # slope
      tm_scale_continuous(
        values = circle_pal,
        limits = c(0, 2 * pi),
        midpoint = pi
      ),                                       # aspect
      tm_scale_continuous(
        values = div_pal,
        midpoint = 0,
        limits = c(-0.15, 0.15),
        outliers.trunc = c(TRUE, TRUE)
      ),                                       # TPI
      tm_scale_continuous(values = cont_pal),  # TRI
      tm_scale_continuous(values = cont_pal),  # TRIriley
      tm_scale_continuous(values = cont_pal),  # TRIrmsd
      tm_scale_continuous(values = cont_pal),  # roughness
      tm_scale_categorical(values = flow_pal)  # flowdir
    ),
    col_alpha = 0.7
  )

# ---- Aside on flow direction----
# flowdir as calculated by terra::terrain() uses a D8 flow algorithm.
# Rather than a direction in degrees or radians, the direction water would flow
# from each cell is encoded as discrete numbers based on powers of 2
# (0 = flat, 1–128 = compass directions clockwise from east). See diagram below.

# 32 64	128
# 16 x  1
# 8  4	2

# ----------------

# Additional packages can be used to derive more LSPs including curvatures, roughness
# measures that are decoupled from slope, and multiscale extensions that aren't restricted
# to a 3x3 focal window. Below we will calculate measures using a 5x5 focal window
# instead of the standard 3x3 window.

# First, we will load the MultiscaleDTM package to provide additional LSP functionality
library(MultiscaleDTM) # Advanced land surface parameters

# SlpAsp() from MultiscaleDTM can be used to calculate multiscale slope and aspect
# including the northness and eastness components of aspect. Here we specify to only
# return slope and aspect in degrees using a 5x5 window.
slp_asp <- SlpAsp(
  ponui_dtm_cropped,
  w = c(5, 5),
  unit = "degrees",
  method = "queen",
  metrics = c("slope", "aspect"),
  na.rm = TRUE
)

# Qfit() from MultiscaleDTM fits a quadratic surface to each focal window so in
# addition to slope and aspect it can calculate LSPs that depend on second order
# derivatives. It can also calculate LSPs based on first order derivatives such
# as slope and aspect but is more computationally expensive than SlpAsp(). Here
# we specify to return three types of curvature: profile (along slope), planform (across slope),
# and twisting curvatures, as well as a classified landform features layer.
qmetrics <- Qfit(
  ponui_dtm_cropped,
  w = c(5, 5),
  metrics = c("profc", "planc", "twistc", "features"),
  na.rm = TRUE
)

slp_curv <- c(slp_asp, qmetrics) # Combine these into one object

hs +
  tm_shape(slp_curv) +
  tm_raster(
    col = names(slp_curv),
    col.scale = list(
      tm_scale_continuous(values = cont_pal),  # slope
      tm_scale_continuous(
        values = circle_pal,
        limits = c(0, 360),
        midpoint = 180
      ),                                       # aspect
      tm_scale_continuous(
        values = div_pal,
        midpoint = 0,
        limits = c(-0.11, 0.08),
        outliers.trunc = c(TRUE, TRUE)
      ),                                       # profc
      tm_scale_continuous(
        values = div_pal,
        midpoint = 0,
        limits = c(-0.09, 0.08),
        outliers.trunc = c(TRUE, TRUE)
      ),                                       # planc
      tm_scale_continuous(
        values = div_pal,
        midpoint = 0,
        limits = c(-0.05, 0.05),
        outliers.trunc = c(TRUE, TRUE)
      ),                                       # twistc
      tm_scale_categorical(values = feat_pal)  # features
    ),
    col_alpha = 0.7
  )

# We can also calculate measure of relative position and roughness using
# the MultiscaleDTM package
# Here we use RelPos() which is a flexible function that can calculate several
# different types of relative position, to calculate the Topographic Position Index.
# Functions TPI(), DMV(), and BPI() are specific measures of relative position
# and are all calls to RelPos() but with different default values.
tpi <- RelPos(
  ponui_dtm_cropped,
  w = c(5, 5),
  shape = "rectangle",
  stand = "none",
  exclude_center = TRUE,
  na.rm = TRUE
) # Topographic Position Index

# Here we will use AdjSD() from MultiscaleDTM to calculate roughness based on
# standard deviation of residuals from a sloping plane.

# All roughness measures within MultiscaleDTM are conceptually decoupled from slope.
# Other roughness measures included but not shown here can be calculated are
# Surface Area to Planar Area Ratio with arc-chord ratio correction (SAPA()),
# Vector Ruggedness Measure (VRM()), and Roughness Index-Elevation (RIE()).
# These can all be calculated using a very similar syntax.

adjsd <- AdjSD(ponui_dtm_cropped, w = c(5, 5), na.rm = TRUE)

# The SurfRough package provides even more additional roughness measures

library(SurfRough) # Advanced Roughness Measures

# The radial roughness index is a modification of the traditional terrain ruggedness index
# that accounts for the influence of slope. It can be calculated using the RRI() function
# in SurfRough and is implemented using a fixed 5x5 cell focal window
rri <- RRI(ponui_dtm_cropped)
names(rri) <- "rri" # add name to layer

# Although not shown here, SurfRough can calculate several vector dispersion based
# roughness measures (similar to MultiscaleDTM::VRM()) using the functions circularDispersionNV(),
# CircularDispersionGV(), and circularEigenNV().

# In addition to these roughness measures, SurfRough can calculate advanced geostatistical
# based roughness measures that provide information on the strength and direction of
# anisotropy in addition to an isotropic overall measure of roughness. This includes
# traditional variogram and madogram based measures via Meanscan() and more robust
# measures based on median absolute differences (MAD) via Madscan().

# Here we use Madscan() to calculate roughness based on the MAD estimator using
# a 5x5 cell focal window and one of the built in kernels that analyzes the
# order 2 differences (as to remove the need for detrending) of adjacent pixels (lag distance of 1)
MAD2ck2 <- Madscan(
  ponui_dtm_cropped,
  kernels = k1ck2,
  w = matrix(data = 1, nrow = 5, ncol = 5)
)
# This measure provides a isotropic roughness strength (IsoRough) similar to
# the other roughness metrics, but also provides a measure of anisotropy (AnisoDir)
# and strength (AnisoR). Anisotropy is measured as the direction of maximum continuity.
# It can only take on values from 90-270 degrees as it is symmetrical so it only
# needs half the circle (e.g. a value of 180 represents anisotropy in the north/south direction).
# Anisotropy strength ranges from 0 to 1.

# ---- Aside on Kernels for Geostatistical Kernels Roughness Measures----
# In addition to a focal window, these measures require the specification of a
# "kernel" specifying the spatial weights for a given direction and lag distance.
# Eight different kernels are implemented by default and it is possible to create
# your own kernels for custom indices. Order 1 kernels require use of a detrended DTM
# (e.g. a relative position surface) and are implemented up until an eight pixel
# lag distance; order 2 kernels do not require detrending and are implemented up
# to a lag distance of two pixels. The implemented order 1 kernels are
# `k1c` (lag 1) `k2c` (lag 2), `k4c` (lag 4), `k6c` (lag 6), and `k8c` (lag 8);
# the implemented order 2 kernels are `k05c` (half pixel lag), `k1ck1` (lag 1)
# and `k2ck2` (lag 2). To get a reliable estimation, a minimum window size
# of 5 x 5 pixels for a square window or a radius of 3 pixels for a circular window is suggested.
# ----------------

tpi_rough <- c(tpi, adjsd, rri, MAD2ck2) # combine into one object

hs +
  tm_shape(tpi_rough) +
  tm_raster(
    col = names(tpi_rough),
    col.scale = list(
      tm_scale_continuous(
        values = div_pal,
        midpoint = 0,
        limits = c(-0.15, 0.15),
        outliers.trunc = c(TRUE, TRUE)
      ),                                        # rpos
      tm_scale_continuous(values = cont_pal),   # adjSD
      tm_scale_continuous(values = cont_pal),   # rri
      tm_scale_continuous(values = cont_pal),   # IsoRough
      tm_scale_continuous(
        values = circle_pal[26:75],
        limits = c(90, 270),
        midpoint = 180
      ),                                        # AnisoDir
      tm_scale_continuous(values = cont_pal)    # AnisoR
    ),
    col_alpha = 0.7
  )

# ==== Correlation and Cluster Analysis ====

# We can leverage R's statistical capabilities to look at the relatedness
# among some of the different LSPs we calculated. To prepare these data
# for the next steps, we will remove the categorical feature layers,
# and decompose any measures that are on a circular scale (aspect and
# anisotropy direction) into their north/south and east/west components
# using cosine and sine respectively.

LSPs <- c(slp_asp, qmetrics, adjsd, rri, MAD2ck2, tpi)
LSPs <- LSPs[[!names(LSPs) %in% c("aspect", "features", "AnisoDir")]]
LSPs$AnisoNorthness <- cos(MAD2ck2$AnisoDir * pi / 180)
LSPs$AnisoEastness <- sin(MAD2ck2$AnisoDir * pi / 180)
LSPs$northness <- cos(slp_asp$aspect * pi / 180)
LSPs$eastness <- sin(slp_asp$aspect * pi / 180)

corr <- layerCor(LSPs, fun = "cor", use = "pairwise.complete.obs") # Calculate correlation
dissimilarity <- as.dist(sqrt(1 - corr$correlation)) # Convert to dissimilarity
hc <- hclust(dissimilarity, method = "ward.D2") # Apply hierarchical clustering

# Clustering result of LSPs
plot(
  hc,
  main = "LSP Clustering",
  xlab = "",
  ylab = "Dissimilarity",
  sub = "",
  cex.main = 0.7,
  cex = 0.6,
  cex.lab = 0.7,
  cex.axis = 0.7
)

cor_data <- reshape2::melt(corr$correlation) # Wrangle data into a data.frame
cor_data <- cor_data |>
  mutate(Keep = as.vector(upper.tri(corr$correlation))) |>
  filter(Keep) # Filter for just one side of the correlation matrix since it's symmetrical

# Correlation plot of LSPs
ggplot(cor_data, aes(x = Var1, y = Var2, fill = value, size = abs(value))) +
  geom_point(shape = 21, color = "black") +
  scale_fill_gradient2(
    low = "blue",
    mid = "white",
    high = "red",
    midpoint = 0
  ) +
  scale_size(range = c(1, 10)) +
  labs(fill = "Correlation", size = "|r|", x = "", y = "") +
  theme_minimal() +
  ggtitle("Correlation") +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    plot.title = element_text(hjust = 0.5, size = 10)
  )
