## ---------------------------
##
## Script name: coregistration_plot.R
##
## Purpose of script: Create coregistration error density plot for Chapter 5 of the Geomorphometry book.
##
## Output: Plot of DEM error density before and after coregistration, saved as PDF and JPG.
##
## Author: Dr. Laurence Hawker
##
## Date Created: 2026-01-26
##
## Copyright (c) Laurence Hawker, 2026
## Email: laurence.hawker.bristol.ac.uk
##
## ---------------------------
##
## Notes: Using the Scientific Colour maps (scico) package for color palettes. The BAM palette is used for the density plot.
##   
##
## ---------------------------

# ---- Required Libraries ----
library(ggplot2)
library(ggpubr)
library(scico)

# ---- Plot dir ----
plot_dir <- 'Path to Figures' # <-- CHANGE THIS TO YOUR FIGURE DIRECTORY

# ---- Synthetic Data Generation ----
set.seed(123)

mean_pre  <- -2.79
rmse_pre  <- 6.740
sd_pre    <- sqrt(rmse_pre^2 - mean_pre^2)

mean_post <- -0.061
rmse_post <- 5.047
sd_post   <- sqrt(rmse_post^2 - mean_post^2)

n_points <- 50000

errors_pre  <- rnorm(n_points, mean = mean_pre,  sd = sd_pre)
errors_post <- rnorm(n_points, mean = mean_post, sd = sd_post)

df <- data.frame(
  Error = c(errors_pre, errors_post),
  Stage = factor(
    rep(c("Before Coregistration", "After Coregistration"),
        each = n_points),
    levels = c("Before Coregistration", "After Coregistration")
  )
)

# ---- Define BAM palette explicitly (order matters!) ----
bam_cols <- scico(2, palette = "bam")
names(bam_cols) <- levels(df$Stage)

# ---- Density Plot ----
p <- ggplot(df, aes(x = Error, fill = Stage, color = Stage)) +
  
  geom_density(alpha = 0.4, linewidth = 1.1) +
  
  # ---- Mean Error Vertical Lines ----
geom_vline(xintercept = mean_pre,
           linetype = "dashed",
           linewidth = 1,
           color = bam_cols["Before Coregistration"]) +
  
  geom_vline(xintercept = mean_post,
             linetype = "dashed",
             linewidth = 1,
             color = bam_cols["After Coregistration"]) +
  
  # ---- Annotations ----
annotate("text",
         x = -20, y = 0.058,
         label = sprintf("Before:\nMean Error = %.3f m\nRMSE = %.3f m",
                         mean_pre, rmse_pre),
         hjust = 0,
         size = 4.2,
         color = bam_cols["Before Coregistration"]) +
  
  annotate("text",
           x = 10, y = 0.058,
           label = sprintf("After:\nMean Error = %.3f m\nRMSE = %.3f m",
                           mean_post, rmse_post),
           hjust = 0,
           size = 4.2,
           color = bam_cols["After Coregistration"]) +
  
  # ---- Scales & Labels ----
scale_fill_manual(values = bam_cols) +
  scale_color_manual(values = bam_cols) +
  
  labs(
    x = "Error (m)",
    y = "Density",
    title = "DEM Error Density Before and After Coregistration"
  ) +
  
  # ---- Theme ----
theme_pubr(base_size = 14) +
  theme(
    legend.position = "top",
    legend.title = element_blank()
  )

# Show plot
p


# ---- Export to PDF ----
ggsave(
  filename = file.path(plot_dir,"Fig_chA05_55.pdf"),
  plot     = p,
  device   = cairo_pdf,
  width    = 7,
  height   = 5,
  units    = "in",
  dpi = 300
)

ggsave(
  filename = file.path(plot_dir,"Fig_chA05_55.jpg"),
  plot     = p,
  width    = 7,
  height   = 5,
  units    = "in",
  dpi = 300
)


# Histogram version below - not used in the book, but can be uncommented if needed.

# ---- Histogram Plot ----

# ggplot(df, aes(x = Error, fill = Stage)) +
#   geom_histogram(position = "identity",
#                  bins     = 100,
#                  alpha    = 0.6,
#                  color    = "black") +
#   
#   # ---- Annotation of Stats ----
# annotate("text", x = -30, y = 4200,
#          label = sprintf("Before: mean = %.3f m\nRMSE = %.3f m",
#                          mean_pre, rmse_pre),
#          hjust = 0, color=scico(1, palette="lajolla")[1], size=4.2) +
#   
#   annotate("text", x = 30, y = 4200,
#            label = sprintf("After: mean = %.3f m\nRMSE = %.3f m",
#                            mean_post, rmse_post),
#            hjust = 0, color=scico(1, palette="lajolla")[2], size=4.2) +
#   
#   # ---- Labels & Scales ----
# scale_fill_scico_d(palette = "lajolla") +
#   labs(x = "Error (m)",
#        y = "Number of points",
#        title = "DEM Error Distribution Before and After Coregistration") +
#   
#   # ---- Theme ----
# theme_pubr(base_size = 14) +
#   theme(legend.position = "top",
#         legend.title = element_blank())
