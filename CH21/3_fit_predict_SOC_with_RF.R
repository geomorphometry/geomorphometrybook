################################################################################
## Title: Fit and predict SOC content using Random forest -----
## Description: Fit a random forest model with target response soil organic 
##              carbon (SOC) content and land surface parameters as predictors, 
##              create variable importance plots and calculate validation with 
##              independent validation data set. Then predict spatial map for 
##              Ponui Island. 
## Date: 26.01.2025
## Author: M. Nussbaum, Utrecht University, Department of Physical Geography 
## Licence: CC-BY 4.0
################################################################################


# load relevant packages 
library(terra)
library(ranger)
library(sf)
library(ggplot2)


# TODO remove
setwd("~/cloud-uu/3_paper_div/2024_geomorphometry/examples_ponui/code_cleaned_for_sharing/")


# 1) Read in and prepare data -----

# create a vector of relevant land surface parameters 
l.rast <- list.files("data/terrain/landsurf_param/", pattern = ".tif$", full.names = T)

# read in training samples 
v.samples <- st_read("results/sampling/cscs_design_150_SOC.gpkg")

# extract land surface parameter pixel values at the 150 sampling locations 
d.covars <- extract(rast(l.rast), v.samples)

# add spatial xy covariates as columns 
d.covars[, c("x", "y")] <- st_coordinates(v.samples)

# Add rotated coordinate axis 
# to allow for spatial trend in more directions than north-south and east-west
# use 30 and 60 degree angular transform 

# create a function (because we will need it later as well).. 
f.add.rotated.xy <- function(d.frame, angles = c(30, 60), x = "x", y = "y") {
  # transform angles from degree to radiant 
  t.rad <- angles * pi / 180
  # create a data frame for each rotation
  l.df.rotations <- lapply(t.rad, function(r) {
    df <- data.frame(
      # angular rotation with standard formula 
      d.frame[, x] * cos(r) - d.frame[, y] * sin(r),
      d.frame[, x] * sin(r) + d.frame[, y] * cos(r)
    )
    # crate meaningful names 
    names(df) <- c( paste0(x, round(r * 180 / pi)),  paste0(y, round(r * 180 / pi)))
    return(df)
  })
  # append all resulting rotation dataframes to original input dataframe 
  cbind(d.frame, do.call(cbind, l.df.rotations))
  # explicit return the dataframe with appended columns 
  return(d.frame)
}

# apply rotation function to our dataframe with response and covariates 
d.covars <- f.add.rotated.xy(d.covars)



# 2) Fit random forest model ----

## fit RF model
m.rf <- ranger(y = v.samples$topsoil_soc,
               x = d.covars[,-c(1)], # Use columns as predictors besides SOC
               importance ="permutation") # Use perm. importance targeting prediction
# print model
m.rf

# Extract predictor importance and order it
t.i <- importance(m.rf)
t.i <- t.i[order(t.i)]

# Create a simple barplot for inspection 
par(oma = c(2,10,2,2))
barplot(t.i, horiz= T, las = 1, cex.names = 0.6)



# 3) Validation with independent sample -----

# read in validation sample 
v.validation <- st_read("results/sampling/strs_design_30_SOC.gpkg")

# extract land surface paratmeter values at sampling locations
d.val.newdata <- extract(rast(l.rast), v.validation)

# add coordinates and rotate them as above 
d.val.newdata[, c("x", "y")] <- st_coordinates(v.validation)
d.val.newdata <- f.add.rotated.xy(d.val.newdata)

# compute random forest prediction for validation locations 
v.validation$pred_soc <- predict(m.rf, d.val.newdata)$prediction


# Scatterplot of predicted vs. observed 
# with 1:1 line and lowess scatterplot smoother
ggplot(v.validation, aes(pred_soc, topsoil_soc)) +
  geom_point(size = 2) + 
  xlab(expression("predicted SOC content [%]")) + 
  ylab(expression("observed SOC content [%]")) +
  ylim(2.5,8.2) + xlim(2.5,8.2) +
  stat_smooth(se = FALSE, span = 1) + 
  geom_abline (slope = 1, linetype = "dashed", color = "black") +
  theme_minimal()

# Compute error statistics 
error <- v.validation$topsoil_soc - v.validation$pred_soc
# mean error*-1 = bias
-1*mean(error)

# root mean squared error
mse <- mean(error^2)
sqrt(mse)

# R2 computed as model efficiency coefficient (deviation against the 1:1 line, not just linear correlation)
1 - ( sum( error^2 ) / sum( (v.validation$topsoil_soc - mean(v.validation$topsoil_soc))^2 ) )



# 4) Compute spatial predictions -----

# Create a dataframe with one pixel = one row, also add xy coordinates
d.newdata <- as.data.frame(rast(l.rast), xy = T, na.rm = T)

# remove missing values
d.newdata <- d.newdata[ complete.cases(d.newdata), ]

# Add rotated coordinates
d.newdata <- f.add.rotated.xy(d.newdata)

# compute prediction for each pixel
d.newdata$pred_soc <- predict(m.rf, d.newdata)$predictions

# create a spatial raster and write to file
r.pred <- rast(d.newdata[, c("x", "y", "pred_soc")], type="xyz", crs= "epsg:2193")
writeRaster(r.pred, filename = "results/mapping/predicted_topsoil_SOC.tif")

