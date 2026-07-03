#!/usr/bin/env Rscript

###############################################################################
# Geomorphometry in GRASS (Chapter 12) - R / rgrass CLI workflow
#
# This script mirrors geomorphometry_in_grass.sh, performing the chapter's
# geomorphometric analyses on the Ponui Island LiDAR data set using the
# `rgrass` package to drive GRASS 8.5+ from R.
#
# It does NOT generate figures - it only creates the analysis rasters and
# vectors. Use geomorphometry_in_grass.py / geomorphometry_in_grass.ipynb
# for the figure-producing workflow.
#
# Requirements:
#   - GRASS 8.5+ available on PATH as `grass`
#   - R package `rgrass` (CRAN)
#   - GRASS add-ons from gextensions.txt (install via g.extension)
#   - Ponui Island data: data/dsm.cog.tif, data/dtm.cog.tif, data/lidar.laz
#     (download from Zenodo - see README.md)
###############################################################################

suppressPackageStartupMessages(library(rgrass))

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
script_path <- tryCatch(
  normalizePath(sys.frame(1)$ofile),
  error = function(e) {
    args <- commandArgs(trailingOnly = FALSE)
    file_arg <- sub("--file=", "", args[grep("--file=", args)])
    if (length(file_arg) > 0) normalizePath(file_arg) else normalizePath("geomorphometry_in_grass.R")
  }
)
PROJECT_DIR <- dirname(script_path)

PROJECT_NAME <- "ponui"
MAPSET_NAME   <- "PERMANENT"
EPSG_CODE     <- "2193"
GISDBASE      <- PROJECT_DIR

# Input data (remote files by default)
DSM_TIF   <- file.path(PROJECT_DIR, "data", "/vsicurl/https://zenodo.org/records/18314107/files/DEM_ponui_island_dsm.tif?download=1")
DTM_TIF   <- file.path(PROJECT_DIR, "data", "/vsicurl/https://zenodo.org/records/18314107/files/DEM_ponui_island_dtm.tif?download=1")

# Input data (local files by default)
# DSM_TIF   <- file.path(PROJECT_DIR, "data", "DEM_ponui_island_dtm.tif")
# DTM_TIF   <- file.path(PROJECT_DIR, "data", "DEM_ponui_island_dtm.tif")
LIDAR_LAZ <- file.path(PROJECT_DIR, "data", "LAS_ponui_island_lidar.laz")
if (!file.exists(LIDAR_LAZ)) {
  stop("FileNotFoundError: The file '", LIDAR_LAZ, "' does not exist.", call. = FALSE)
}

# Raster names used throughout the workflow
DSM_NAME             <- "dsm_10m"
DTM_NAME             <- "dem_10m"
DTM_RELIEF           <- "dtm_relief"
LIDAR_DTM_10M        <- "lidar_dtm_10m"
LIDAR_DTM_1M         <- "lidar_dtm_1m"
LIDAR_DTM_1M_RELIEF  <- "lidar_dtm_1m_relief"

AOI_REGION  <- "aoi"
AOI_RES     <- 1
ISLAND_RES  <- 10

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
require_file <- function(path) {
  if (!file.exists(path)) {
    stop(sprintf("Missing input file: %s", path), call. = FALSE)
  }
}

have_module <- function(mod) {
  # Check whether a GRASS module is callable in the current session.
  res <- tryCatch(
    execGRASS(mod, flags = "help", ignore.stderr = TRUE, ignore.stdout = TRUE,
              intern = TRUE, echoCmd = FALSE),
    error = function(e) NULL
  )
  !is.null(res)
}

warn_missing_addon <- function(mod) {
  message(sprintf(
    "WARNING: GRASS module '%s' not found; skipping related step.\n         Install add-ons listed in CH12/gextensions.txt if needed.",
    mod
  ))
}

find_gisbase <- function() {
  gisbase <- Sys.getenv("GISBASE", unset = "")
  if (nzchar(gisbase) && dir.exists(gisbase)) return(gisbase)

  grass_bin <- Sys.which("grass")
  if (!nzchar(grass_bin)) {
    stop(
      "Could not find the `grass` executable on PATH. ",
      "Install GRASS 8.5+ or set GISBASE manually.",
      call. = FALSE
    )
  }
  out <- system2(grass_bin, c("--config", "path"), stdout = TRUE)
  if (length(out) == 0 || !dir.exists(out[1])) {
    stop("`grass --config path` did not return a usable GISBASE.", call. = FALSE)
  }
  out[1]
}

# -----------------------------------------------------------------------------
# GRASS session bootstrap
# -----------------------------------------------------------------------------
require_file(DSM_TIF)
require_file(DTM_TIF)
require_file(LIDAR_LAZ)

gisbase <- find_gisbase()
project_path <- file.path(GISDBASE, PROJECT_NAME)
if (!dir.exists(project_path)) {
  message(sprintf("Creating GRASS project at: %s (EPSG:%s)",
                  project_path, EPSG_CODE))
  system2("grass", c("-c", paste0("EPSG:", EPSG_CODE), "-e", project_path))
}

initGRASS(
  gisBase  = gisbase,
  gisDbase = GISDBASE,
  location = PROJECT_NAME,
  mapset   = MAPSET_NAME,
  override = TRUE,
  home     = tempdir()
)

message("Running inside GRASS session.")
execGRASS("g.gisenv")

# -----------------------------------------------------------------------------
# 1) Import base rasters + 10m LiDAR mean DTM
# -----------------------------------------------------------------------------
message(sprintf("Importing DSM/DTM (%dm) and LiDAR mean DTM...", ISLAND_RES))

execGRASS("r.import",
  input = DSM_TIF, output = DSM_NAME,
  resample = "bilinear", resolution = "value",
  resolution_value = as.character(ISLAND_RES),
  title = sprintf("Ponui Island %dm DSM", ISLAND_RES),
  flags = "quiet"
)

execGRASS("r.import",
  input = DTM_TIF, output = DTM_NAME,
  resample = "bilinear", resolution = "value",
  resolution_value = as.character(ISLAND_RES),
  title = sprintf("Ponui Island %dm DTM", ISLAND_RES),
  flags = "quiet"
)

# LiDAR mean raster at island resolution
execGRASS("r.in.pdal",
  input = LIDAR_LAZ, output = LIDAR_DTM_10M,
  method = "mean", resolution = as.character(ISLAND_RES),
  class_filter = "2",
  flags = c("w", "e", "quiet")
)

# Set ocean values (< 0) to NULL
execGRASS("r.null", map = DTM_NAME,       setnull = "-9999-0", flags = "quiet")
execGRASS("r.null", map = DSM_NAME,       setnull = "-9999-0", flags = "quiet")
execGRASS("r.null", map = LIDAR_DTM_10M,  setnull = "-9999-0", flags = "quiet")

# Region to island DTM
execGRASS("g.region", raster = DTM_NAME, flags = "a")

message("Computing relief (island)...")
execGRASS("r.relief", input = DTM_NAME, output = DTM_RELIEF, flags = "quiet")

message("Computing 2nd order derivatives (island)...")
execGRASS("r.slope.aspect",
  elevation  = DTM_NAME,
  slope      = paste0(DTM_NAME, "_slope"),
  aspect     = paste0(DTM_NAME, "_aspect"),
  pcurvature = paste0(DTM_NAME, "_pcurv"),
  tcurvature = paste0(DTM_NAME, "_tcurv"),
  dx         = paste0(DTM_NAME, "_dx"),
  dy         = paste0(DTM_NAME, "_dy"),
  flags = "quiet"
)

# Resample to coarser resolutions (analysis outputs only)
for (res in c(150, 250, 500)) {
  message(sprintf("Resampling %s to %dm...", DTM_NAME, res))
  execGRASS("g.region", res = as.character(res), raster = DTM_NAME)
  execGRASS("r.resamp.interp",
    input  = DTM_NAME,
    output = sprintf("%s_%dm", DTM_NAME, res),
    method = "bilinear",
    flags  = "quiet"
  )
}

# -----------------------------------------------------------------------------
# 2) AOI: region, LiDAR processing, interpolation, derivatives
# -----------------------------------------------------------------------------
message(sprintf("Setting AOI region (%dm)...", AOI_RES))
execGRASS("g.region",
  n = "5918600.13", s = "5917599.13",
  w = "1793519.48", e = "1794520.48",
  res = as.character(AOI_RES),
  flags = c("a", "p")
)
execGRASS("g.region", save = AOI_REGION)

# AOI boundary vector (useful for debugging and optional masking)
execGRASS("v.in.region", output = AOI_REGION, type = "area", flags = "quiet")

execGRASS("g.region", region = AOI_REGION, res = as.character(AOI_RES), flags = "a")

message("Importing LiDAR ground points (vector)...")
execGRASS("v.in.pdal",
  input = LIDAR_LAZ, output = "lidar_be",
  class_filter = "2",
  flags = c("o", "r", "quiet")
)

message("Counting LiDAR points per cell (1m)...")
execGRASS("r.in.pdal",
  input = LIDAR_LAZ, output = "lidar_dtm_n_1m",
  method = "n", resolution = "1", class_filter = "2",
  flags = c("w", "e", "quiet")
)

message("Interpolating LiDAR DTM (RST)...")
execGRASS("v.surf.rst",
  input      = "lidar_be",
  elevation  = LIDAR_DTM_1M,
  slope      = paste0(LIDAR_DTM_1M, "_rst_slope"),
  aspect     = paste0(LIDAR_DTM_1M, "_rst_aspect"),
  pcurvature = paste0(LIDAR_DTM_1M, "_rst_pcurv"),
  tcurvature = paste0(LIDAR_DTM_1M, "_rst_tcurv"),
  mcurvature = paste0(LIDAR_DTM_1M, "_rst_mcurv"),
  tension = "300", smooth = "0.1", npmin = "200",
  dmin = "1.5", nprocs = "30",
  flags = c("t", "quiet")
)

execGRASS("r.null", map = LIDAR_DTM_1M, setnull = "-9999-0", flags = "quiet")

message("Relief + derivatives (AOI LiDAR DTM)...")
execGRASS("r.relief",
  input = LIDAR_DTM_1M, output = LIDAR_DTM_1M_RELIEF, flags = "quiet"
)

execGRASS("r.slope.aspect",
  elevation  = LIDAR_DTM_1M,
  slope      = paste0(LIDAR_DTM_1M, "_slope"),
  aspect     = paste0(LIDAR_DTM_1M, "_aspect"),
  pcurvature = paste0(LIDAR_DTM_1M, "_pcurv"),
  tcurvature = paste0(LIDAR_DTM_1M, "_tcurv"),
  dx         = paste0(LIDAR_DTM_1M, "_dx"),
  dy         = paste0(LIDAR_DTM_1M, "_dy"),
  flags = "quiet"
)

# Optional: edge-preserving smoothing (module availability depends on build)
if (have_module("r.smooth.edgepreserve")) {
  message("Smoothing LiDAR DTM (edge-preserving Tukey)...")
  execGRASS("r.smooth.edgepreserve",
    input      = LIDAR_DTM_1M,
    output     = paste0(LIDAR_DTM_1M, "_s_agg_tukey"),
    `function` = "tukey",
    threshold = "15", lambda = "0.4", steps = "20",
    flags = "quiet"
  )

  execGRASS("r.slope.aspect",
    elevation  = paste0(LIDAR_DTM_1M, "_s_agg_tukey"),
    slope      = paste0(LIDAR_DTM_1M, "_s_agg_tukey_slope"),
    aspect     = paste0(LIDAR_DTM_1M, "_s_agg_tukey_aspect"),
    pcurvature = paste0(LIDAR_DTM_1M, "_s_agg_tukey_pcurv"),
    tcurvature = paste0(LIDAR_DTM_1M, "_s_agg_tukey_tcurv"),
    dx         = paste0(LIDAR_DTM_1M, "_s_agg_tukey_dx"),
    dy         = paste0(LIDAR_DTM_1M, "_s_agg_tukey_dy"),
    flags = "quiet"
  )
} else {
  message("NOTE: r.smooth.edgepreserve not found; skipping smoothing.")
}

# -----------------------------------------------------------------------------
# 3) Hydrology: flow accumulation, TWI, streams, HAND
# -----------------------------------------------------------------------------
message("Computing flow accumulation methods...")

# D8 MFD
execGRASS("r.watershed",
  elevation    = LIDAR_DTM_1M,
  accumulation = "d8_mfd_flowaccum",
  drainage     = "d8_mfd_flowdir",
  stream       = "d8_mfd_streams",
  basin        = "d8_mfd_basins2",
  threshold    = "100000",
  flags = c("a", "4", "quiet")
)

# D8 SFD
execGRASS("r.watershed",
  elevation    = LIDAR_DTM_1M,
  accumulation = "d8_sfd_flowaccum",
  drainage     = "d8_sfd_flowdir",
  threshold    = "100000",
  flags = c("s", "a", "quiet")
)

# D-infinity SFD
execGRASS("r.flow",
  elevation = LIDAR_DTM_1M,
  flowaccumulation = "dinf_sfd_flowaccum",
  flags = "quiet"
)
execGRASS("r.null", map = "dinf_sfd_flowaccum", setnull = "-9999-0", flags = "quiet")

# MEFA (add-on r.flowaccumulation)
if (have_module("r.flowaccumulation")) {
  execGRASS("r.flowaccumulation",
    input  = "d8_sfd_flowdir",
    format = "45degree",
    output = "MEFA_flowaccum",
    type   = "CELL",
    flags  = "quiet"
  )
} else {
  warn_missing_addon("r.flowaccumulation")
}

message("Computing TWI...")
execGRASS("r.mapcalc",
  expression = sprintf(
    "twi = log(d8_mfd_flowaccum / tan(%s_slope * 3.14159 / 180))",
    LIDAR_DTM_1M
  ),
  flags = "quiet"
)

message("Delineating streams + stream order...")
if (have_module("r.stream.order") && have_module("r.stream.extract")) {
  execGRASS("r.thin",
    input = "d8_mfd_streams", output = "d8_mfd_streams_thin", flags = "quiet"
  )
  execGRASS("r.to.vect",
    input = "d8_mfd_streams_thin", output = "d8_mfd_streams", type = "line",
    flags = "quiet"
  )

  execGRASS("r.stream.extract",
    elevation     = LIDAR_DTM_1M,
    threshold     = "5000",
    direction     = "stream_extract_dir",
    stream_raster = "stream_extract",
    stream_vector = "stream_extract",
    flags = "quiet"
  )

  execGRASS("r.stream.order",
    elevation    = LIDAR_DTM_1M,
    accumulation = "d8_mfd_flowaccum",
    direction    = "stream_extract_dir",
    stream_rast  = "stream_extract",
    stream_vect  = "stream_orders",
    strahler     = "strahler",
    horton       = "horton",
    flags = "quiet"
  )
} else {
  warn_missing_addon("r.stream.order")
  warn_missing_addon("r.stream.extract")
}

message("Running HAND workflow...")
if (have_module("r.hand")) {
  execGRASS("r.hand",
    elevation          = LIDAR_DTM_1M,
    threshold          = "50000",
    inundation_raster  = "inundation",
    inundation_strds   = "inundation_strds",
    start_water_level  = "0",
    end_water_level    = "5",
    water_level_step   = "0.5",
    hand               = "hand",
    flags = c("t", "quiet")
  )
} else {
  warn_missing_addon("r.hand")
}

# -----------------------------------------------------------------------------
# 4) Overland flow + erosion/deposition (masked to basin)
# -----------------------------------------------------------------------------
message("Converting basins raster to vector for masking...")
execGRASS("r.to.vect",
  input = "d8_mfd_basins2", output = "d8_mfd_basins2", type = "area",
  flags = "quiet"
)

message("Masking to basin and running r.sim.water / r.sim.sediment...")
execGRASS("r.mask", vector = "d8_mfd_basins2", flags = "quiet")

execGRASS("r.sim.water",
  elevation = LIDAR_DTM_1M,
  dx = paste0(LIDAR_DTM_1M, "_dx"),
  dy = paste0(LIDAR_DTM_1M, "_dy"),
  rain_value = "30", infil_value = "0.0", man_value = "0.2",
  niterations = "30", output_step = "2",
  depth = "depth", discharge = "disch",
  random_seed = "3", nwalkers = "100000", nprocs = "6",
  flags = "t"
)

execGRASS("r.mapcalc",
  expression = "max_depth = if(depth.30 >= 0.01, depth.30, null())",
  flags = "quiet"
)

# Sediment transport / erosion-deposition
execGRASS("r.mapcalc", expression = "tranin = 0.001",     flags = "quiet")
execGRASS("r.mapcalc", expression = "detin = 0.001",      flags = "quiet")
execGRASS("r.mapcalc", expression = "shear_stress = 0.5", flags = "quiet")

execGRASS("r.sim.sediment",
  elevation = LIDAR_DTM_1M,
  dx = paste0(LIDAR_DTM_1M, "_dx"),
  dy = paste0(LIDAR_DTM_1M, "_dy"),
  water_depth = "depth.30",
  detachment_coeff = "detin", transport_coeff = "tranin",
  shear_stress = "shear_stress", man_value = "0.04",
  transport_capacity = "transport_capacity",
  tlimit_erosion_deposition = "tlimit_erosion_deposition",
  sediment_concentration = "sediment_concentration",
  sediment_flux = "sediment_flux",
  erosion_deposition = "erosion_deposition",
  niterations = "30", output_step = "2",
  random_seed = "3", nprocs = "26", nwalkers = "100000"
)

execGRASS("r.mask", flags = c("r", "quiet"))

# -----------------------------------------------------------------------------
# 5) Solar radiation, TPI, landforms
# -----------------------------------------------------------------------------
message("Computing solar radiation (r.sun)...")
execGRASS("r.sun",
  elevation = LIDAR_DTM_1M,
  slope  = paste0(LIDAR_DTM_1M, "_slope"),
  aspect = paste0(LIDAR_DTM_1M, "_aspect"),
  glob_rad   = "global_rad_356",
  insol_time = "insol_time_356",
  day = "356",
  flags = "quiet"
)

execGRASS("r.sun",
  elevation = LIDAR_DTM_1M,
  slope  = paste0(LIDAR_DTM_1M, "_slope"),
  aspect = paste0(LIDAR_DTM_1M, "_aspect"),
  glob_rad   = "global_rad_172",
  insol_time = "insol_time_172",
  day = "172",
  flags = "quiet"
)

if (have_module("r.tpi")) {
  message("Computing TPI...")
  execGRASS("r.tpi", input = LIDAR_DTM_1M, output = "tpi", flags = "quiet")
} else {
  warn_missing_addon("r.tpi")
}

message("Computing landforms + morphology...")
if (have_module("r.geomorphon")) {
  execGRASS("r.geomorphon",
    elevation = LIDAR_DTM_1M,
    forms     = paste0(LIDAR_DTM_1M, "_landforms"),
    search = "21", skip = "1", flat = "1", dist = "0",
    flags = "quiet"
  )
} else {
  warn_missing_addon("r.geomorphon")
}

if (have_module("r.param.scale")) {
  execGRASS("r.param.scale",
    input  = LIDAR_DTM_1M,
    output = paste0(LIDAR_DTM_1M, "_morphology"),
    method = "feature", size = "5",
    flags = "quiet"
  )
} else {
  warn_missing_addon("r.param.scale")
}

message(sprintf("Done. Analysis rasters are now in: %s/%s",
                project_path, MAPSET_NAME))
