### Install the following packages if necessary:
# install.packages("mgcv")
# install.packages("ROCR")

library("mgcv")  # GAM
library("ROCR")  # AUROC estimation

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

data <- read.csv("susc_slopeunits_gam/input/susc_slopeunits.csv", sep = ";")

# Do some data exploration:
hist(data$pcurv_average) # etc.

# Trim variables that have outliers or extremely long tails:
data$slope_average[ data$slope_average > 60] <- 60
data$pcurv_average[ data$pcurv_average < -0.003] <- -0.003
data$pcurv_average[ data$pcurv_average > 0.002] <- 0.002
data$pcurv_stddev[ data$pcurv_stddev > 0.03] <- 0.03
data$twi_average[ data$twi_average < 4] <- 4
data$twi_average[ data$twi_average > 8] <- 8
data$twi_stddev[ data$twi_stddev < 1] <- 1
data$twi_stddev[ data$twi_stddev > 3] <- 3

# Initial model formula with all predictors:
formula_slides = slides ~
 s(slope_average) +
 s(slope_stddev) +
 s(pcurv_average) +
 s(pcurv_stddev) +
 s(twi_average) +
 s(twi_stddev) +
 s(nthns_average) +
 s(nthns_stddev) +
 s(easns_average) +
 s(easns_stddev) +
 # one class is redundant, used as reference level:
 # perc_geo_1 +
 perc_geo_2 +
 perc_geo_3 +
 perc_geo_4 +
 perc_geo_5

# Names of predictor variables:
predictors <- all.vars(formula_slides)[-1]

# Take a look at pairwise Spearman correlations:
round(cor(data[,predictors], method = "spearman"), 2)

# Take a look at conditional density plots
# (use spineplot() or cdplot()):
spineplot(data$slope_average, factor(data$slides))
spineplot(data$slope_stddev, factor(data$slides))
# etc.

# Initial model, with variable selection through shrinkage:
fit <- mgcv::gam(formula_slides, family = binomial, 
                 data = data, select = TRUE)
# Note that some edf are very small (<<1):
summary(fit)


# Revised formula (after two iterations of eliminating
# predictors with edf << 1 and limiting the edf to
# avoid overfitting):

formula_slides = slides ~
  s(slope_average, k = 4) +
  # s(slope_stddev, k = 4) +
  s(pcurv_average, k = 4) +
  # s(pcurv_stddev) +
  s(twi_average, k = 4) +
  s(twi_stddev) +
  s(nthns_average, k = 4) +
  # s(nthns_stddev) +
  # s(easns_average) +
  s(easns_stddev) +
  # perc_geo_1 +
  perc_geo_2 +
  perc_geo_3 +
  perc_geo_4 +
  perc_geo_5

# Fit final model:
fit <- mgcv::gam(formula_slides, family = binomial, 
                 data = data, select = TRUE)

summary(fit)
# Note that p-values are invalid due to variable selection!

# Goodness of fit on the training set:
auroc(pred = fit$fitted.values, obs = data$slides == 1, plot = TRUE)

# Transformation plots:
par(mfrow = c(2,5))
plot(fit, residuals = FALSE, all.terms = TRUE, shade=TRUE,
     shade.col="grey", seWithMean = FALSE, main = "", ylim = c(-4,4))

# Are there concurvity issues?
concurvity(fit)
# High value for parametric terms is related to the distrubution
# of perc_geol variables.
# Moderately high values for slope_average and twi_average can
# be explained by the relatively strong correlation of these
# two variables.

gam.check(fit)
# No clear indication of under-fitting.

# Reduction of explained deviance when removing predictors:
dev.expl <- summary(fit)$dev.expl
1 - summary(update(fit, . ~ . - s(slope_average, k = 4)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(pcurv_average, k = 4)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(twi_average, k = 4)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(twi_stddev)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(nthns_average, k = 4)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - s(easns_stddev)))$dev.expl / dev.expl
1 - summary(update(fit, . ~ . - perc_geo_2 - perc_geo_3 - perc_geo_4 - perc_geo_5))$dev.expl / dev.expl



# GLM, fitted using the mgcv::gam function:
fit_glm <- gam(slides ~ slope_average + pcurv_average + twi_average + twi_stddev + nthns_average + easns_stddev + perc_geo_2 + perc_geo_3 + perc_geo_4 + perc_geo_5, family = binomial, data = data)
summary(fit_glm)

# Goodness of fit on the training set:
auroc(pred = fit_glm$fitted.values, obs = data$slides == 1, plot = TRUE)



##GAM SUSCEPTIBILITY VALUE

susc_map <- data.frame(SU_ID = data$cat, susc = fit$fitted.values)
write.table(susc_map,file ="susc_slopeunits_gam/output/susc_slopeunits_fit_gam.csv", col.names = T, row.names = F, sep = ";")

##GLM SUSCEPTIBILITY VALUE

susc_map_glm <- data.frame(SU_ID = data$cat, susc = fit_glm$fitted.values)
write.table(susc_map_glm,file ="susc_slopeunits_gam/output/susc_slopeunits_fit_glm.csv", col.names = T, row.names = F, sep = ";")

