### Install the following packages if necessary:
# install.packages("mgcv")
# install.packages("ROCR")

library("mgcv")
library("ROCR")           # AUROC estimation

# A function for plotting ROC curves and
# calculating the area under the ROC curve (AUROC)
# using the ROCR package:
auroc <- function(pred, obs, plot=FALSE) {
  stopifnot(is.logical(obs) | is.factor(obs))
  stopifnot(is.numeric(pred))
  stopifnot(length(pred) == length(obs))
  if (is.factor(obs)) stopifnot(nlevels(obs)==2)
  predobj <- prediction( pred, obs )
  if (plot) plot(performance(predobj, "tpr", "fpr"))
  auroc <- performance( predobj, measure="auc" )@y.values[[1]]
  return(auroc)
}

data <- read.csv("susc_grid_gam/input/susc_grid.csv", sep = ";")

summary(data)

data$geology <- factor(data$geology)
table(data$geology)

data$pcurv[ data$pcurv < (-0.03) ] <- -0.03
data$pcurv[ data$pcurv > 0.03 ] <- 0.03

data$twi[ data$twi > 11 ] <- 11


num_predictors <- c("slope", "twi", "pcurv",
                    "relief_3", "relief_5", "relief_7", "relief_9", 
                    "nthns", "easns")

round(cor(data[,num_predictors], method = "spearman"), 2)
# Correlations >0.94 for relief_* variables -> pick only relief_9

# Prefer a log-transformed and trimmed version of relief_9:
data$log10_relief_9 <- log10(data$relief_9)
data$log10_relief_9[data$log10_relief_9 < 0.5] <- 0.5

# Take a look at conditional density plots
# (use spineplot() or cdplot()):
spineplot(data$slope, factor(data$slides))
spineplot(data$pcurv, factor(data$slides))
# etc.



formula_slides <- slides ~
  s(slope) +
  s(twi) +
  s(log10_relief_9)+ 
  s(pcurv) +
  s(nthns) + 
  s(easns) +
  geology

fit <- mgcv::gam(formula_slides, family = binomial, 
                       data = data, select = TRUE)
summary(fit)
plot(fit, pages = 1, residuals = FALSE, all.terms = TRUE, shade = TRUE,
     shade.col = "grey", seWithMean = FALSE, main = "", ylim = c(-4,4))


formula_slides <- slides ~
  s(slope) +
  s(twi) +
  s(log10_relief_9, k = 4)+ 
  s(pcurv, k = 4) +
  geology

fit <- mgcv::gam(formula_slides, family = binomial, 
                       data = data)

# par(mfrow = c(1,4))
par(mfrow = c(2,3))
plot(fit, residuals = FALSE, all.terms = TRUE, shade = TRUE,
     shade.col = "grey", seWithMean = FALSE, main = "", ylim = c(-4,4))

summary(fit)

# Goodness of fit on the training set:
auroc(pred = fit$fitted.values, obs = data$slides == 1, plot = TRUE)

# Concurvity checks:
concurvity(fit)

# Check for possible underfitting:
gam.check(fit)

# Reduction of explained deviance when removing predictors:
dev.expl <- summary(fit)$dev.expl
1 - summary(update(fit, . ~ . - s(slope)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(twi)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(log10_relief_9, k = 4)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(pcurv, k = 4)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - geology))$dev.expl / dev.expl

# GLM, fitted using the mgcv::gam function:
fit_glm <- gam(slides ~ slope + twi + log10_relief_9 + pcurv + geology, 
               family = binomial, data = data)
summary(fit_glm)

# Goodness of fit on the training set:
auroc(pred = fit_glm$fitted.values, obs = data$slides == 1, plot = TRUE)

#
# PREDICT
#

library("terra")

grd_slope <- terra::rast("susc_grid_gam/input/slope.gpkg")
names(grd_slope) <- "slope"
grd_pcurv <- terra::rast("susc_grid_gam/input/pcurv.gpkg")
names(grd_pcurv) <- "pcurv"
grd_twi <- terra::rast("susc_grid_gam/input/twi.gpkg")
names(grd_twi) <- "twi"
grd_relief_9 <- terra::rast("susc_grid_gam/input/relief_9.gpkg")
names(grd_relief_9) <- "relief_9"
grd_geology <- terra::rast("susc_grid_gam/input/geology.gpkg")
names(grd_geology) <- "geology"

grd_pcurv[ grd_pcurv < (-0.03) ] <- -0.03
grd_pcurv[ grd_pcurv > 0.03 ] <- 0.03

grd_twi[ grd_twi > 11 ] <- 11

grd_log10_relief_9 <- log10(grd_relief_9)
names(grd_log10_relief_9) <- "log10_relief_9"
grd_log10_relief_9[grd_log10_relief_9 < 0.5] <- 0.5

preddata <- c(
  grd_slope, 
  grd_pcurv, 
  grd_twi, 
  grd_log10_relief_9, 
  grd_geology)

preddata$gampred <- terra::predict(preddata, fit, type = "response")
plot(preddata$gampred)

preddata$glmpred <- terra::predict(preddata, fit_glm, type = "response")
plot(preddata$glmpred)

#terra::writeRaster(
#  x = preddata["gampred"], 
#  filename = "susc_grid_gam/output/gampred.tif", 
#  overwrite = TRUE)

#terra::writeRaster(
#  x = preddata["glmpred"], 
#  filename = "susc_grid_gam/output/glmpred.tif", 
#  overwrite = TRUE)

terra::writeRaster(
  x = preddata["gampred"], 
  filename = "susc_grid_gam/output/gampred.gpkg", 
  overwrite = TRUE)

terra::writeRaster(
  x = preddata["glmpred"], 
  filename = "susc_grid_gam/output/glmpred.gpkg", 
  overwrite = TRUE)

