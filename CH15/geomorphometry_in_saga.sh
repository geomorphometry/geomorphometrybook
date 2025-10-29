#!/bin/bash

#################################################################################
# MIT License

# Copyright (c) 2024 Olaf Conrad, Volker Wichmann

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#################################################################################


#################################################################################
#
# This script supplements the chapter "Geomorphometry in SAGA" from the
# Geomorphometry book and generates the data sets presented there for
# Ponui Island. This script has been worked out with SAGA 9.7.
# 
# In order to run the script, the path to the input LAS file must be adjusted
# in the "Configuration" section. Under MacOS, if you use the SAGA-Application
# Bundle, also the path to "saga_cmd" must be configured (see below).
#
# The script performs the following calculations: (i) DEM creation from the point
# cloud, (ii) contour line calculation, (iii) morphometric analysis,
# (iv) relief classification and (v) hydological analysis.
#
#################################################################################

# _____________________________________
# #####################################
# Configuration

# MacOS: If you are using the SAGA-Application-Bundle you
# need to add the directory including the saga_cmd application
# to your system's PATH variable. Just uncomment the following
# line and adjust the path accordingly if necessary:
###PATH=/Applications/SAGA.app/Contents/MacOS/:$PATH

# Where is the point cloud file to be processed?
FILE_LAS="$(pwd)/ponui.laz"

# Set target cellsize and file names
CELLSIZE=5

# Choose a directory for storing the results.
WORKDIR="$(pwd)/results_"$CELLSIZE"m"
if [ ! -d "$WORKDIR" ]; then
    mkdir "$WORKDIR"
fi
cd "$WORKDIR"

# _____________________________________
# #####################################
# Digital Surface Model (Ground, Buildings, Vegetation)

# _____________________________________
# [Import Grid from Point Cloud]
# Use all valid points (ground, buildings, low/mid/high vegetation: classes = 2, 3, 4, 5, 6).
# Request maximum value if more than one point falls into a target cell (aggregation).
# Set target cellsize, target extent will be fitted to the points data.
saga_cmd io_pdal 2 \
 -FILES=\""$FILE_LAS"\" \
 -CLASSES=\"2,3,4,5,6\" \
 -AGGREGATION=\"maximum\" \
 -TARGET_DEFINITION=\"user defined\" \
 -TARGET_USER_SIZE=$CELLSIZE \
 -GRID=\"dsm.tif\"

# _____________________________________
# [Set Coordinate Reference System]
# LAS file does not know about its CRS ...but we do!
saga_cmd pj_proj4 0 \
 -CRS_STRING=\"epsg:2193\" \
 -GRIDS=\"dsm.tif\" \
 -GRIDS_OUT=\"dsm.tif\"

# _____________________________________
# [Shrink and Expand]
# Closing gaps, result overwrites input raster.
saga_cmd grid_tools 28 \
 -INPUT=\"dsm.tif\" \
 -RESULT=\"dsm.tif\" \
 -OPERATION=\"expand and shrink\" \
 -RADIUS=6 \
 -EXPAND=\"maximum\"

# _____________________________________
# #####################################
# Digital Terrain Model (Ground)

# _____________________________________
# [Import Grid from Point Cloud]
# Use ground points only (class = 2).
# Request mean value if more than one point falls into a target cell (aggregation).
# Take the same grid system as used by the surface model (target template = DSM).
saga_cmd io_pdal 2 \
 -FILES=\""$FILE_LAS\"" \
 -CLASSES=\"2\" \
 -AGGREGATION=\"mean\" \
 -TARGET_DEFINITION=1 \
 -TARGET_TEMPLATE=\"dsm.tif\" \
 -GRID=\"dtm.tif\"

# _____________________________________
# [Set Coordinate Reference System]
# LAS file does not know about its CRS ...but we do!
saga_cmd pj_proj4 0 \
 -CRS_STRING=\"epsg:2193\" \
 -GRIDS=\"dtm.tif\" \
 -GRIDS_OUT=\"dtm.tif\"

# _____________________________________
# [Multilevel B-Spline from Grid Points]
# Create a DEM free of gaps using spline interpolation.
saga_cmd grid_spline 5 \
 -TARGET_DEFINITION=1 \
 -TARGET_TEMPLATE=\"dtm.tif\" \
 -TARGET_OUT_GRID=\"dtm_splined.tif\" \
 -GRID=\"dtm.tif\"

# _____________________________________
# [Grid Masking]
# Apply the DSM as land mask.
saga_cmd grid_tools 24 \
 -GRID=\"dtm_splined.tif\" \
 -MASKED=\"dtm_splined.tif\" \
 -MASK=\"dsm.tif\"

# _____________________________________
# [Patching]
# Fill any gaps with interpolated values.
saga_cmd grid_tools 5 \
 -ORIGINAL=\"dtm.tif\" \
 -COMPLETED=\"dtm.tif\" \
 -ADDITIONAL=\"dtm_splined.tif\" \
 -RESAMPLING=3

# _____________________________________
# [Grid Calculator]
# Calculate the difference between DSM and DTM.
saga_cmd grid_calculus 1 \
 -FORMULA=\""g1 - g2"\" \
 -GRIDS=\""dsm.tif;dtm.tif"\" \
 -RESULT=\"height_above_ground.tif\"

# _____________________________________
# #####################################
# Contour Lines

# _____________________________________
# [Countour Lines from Grid]
saga_cmd shapes_grid 5 \
 -GRID=\"dtm.tif\" \
 -CONTOUR=\"contours_10m.geojson\" \
 -ZSTEP=10

# _____________________________________
# [Countour Lines from Grid]
saga_cmd shapes_grid 5 \
 -GRID=\"dtm.tif\" \
 -CONTOUR=\"contours_50m.geojson\" \
 -ZSTEP=50

# _____________________________________
# #####################################
# Examples: Morphometry

# _____________________________________
# [Analytical Hillshading]
saga_cmd ta_lighting 0 \
 -ELEVATION=\"dtm.tif\" \
 -SHADE=\"shading.tif\" \
 -AZIMUTH=315 -DECLINATION=45 -EXAGGERATION=1

# _____________________________________
# [Slope, Aspect, Curvature]
saga_cmd ta_morphometry 0 \
 -ELEVATION=\"dtm.tif\" \
 -SLOPE=\"slope.tif\" \
 -ASPECT=\"aspect.tif\" \
 -C_PROF=\"curvature_profile.tif\" \
 -C_PLAN=\"curvature_plan.tif\" \
 -METHOD=\""9 parameter 2nd order polynom (Zevenbergen & Thorne 1987)"\" \
 -UNIT_SLOPE=\"degree\" -UNIT_ASPECT=\"degree\"

# _____________________________________
# [Topographic Position Index]
saga_cmd ta_morphometry 18 \
 -DEM=\"dtm.tif\" \
 -TPI=\"tpi.tif\"

# _____________________________________
# [Topographic Openness]
saga_cmd ta_lighting 5 \
 -DEM=\"dtm.tif\" \
 -POS=\"openness_positive.tif\" \
 -NEG=\"openness_negative.tif\"

# _____________________________________
# #####################################
# Examples: Relief Classification

# _____________________________________
# [Curvature Classification]
saga_cmd ta_morphometry 4 \
 -DEM=\"dtm.tif\" \
 -CLASSES=\"classes_curvature.tif\" \
 -STRAIGHT=175.0 -SMOOTH=10

# _____________________________________
# [Geomorphons]
saga_cmd ta_lighting 8 \
 -DEM=\"dtm.tif\" \
 -GEOMORPHONS=\"classes_geomorphons.tif\" \
 -THRESHOLD=1.0 -RADIUS=150.0

# _____________________________________
# [TPI Based Landform Classification]
saga_cmd ta_morphometry 19 \
 -DEM=\"dtm.tif\" \
 -LANDFORMS=\"classes_landforms.tif\" \
 -RADIUS_A_MAX=25.0 \
 -RADIUS_B_MAX=150.0

# _____________________________________
# [Morphometric Features]
saga_cmd ta_morphometry 23 \
 -DEM=\"dtm.tif\" \
 -FEATURES=\"classes_morphometric_features.tif\" \
 -SIZE=10 -TOL_SLOPE=10.0 -TOL_CURVE=0.005 -EXPONENT=0 -ZSCALE=1 -CONSTRAIN=1

# _____________________________________
# #####################################
# Examples: Hydrology

# _____________________________________
# [Fill Sinks (Wang & Liu)]
saga_cmd ta_preprocessor 5 \
 -ELEV=\"dtm.tif\" \
 -FILLED=\"dtm_nosinks.tif\" \
 -MINSLOPE=0.1

# _____________________________________
# [Flow Accumulation (Top-Down)]
saga_cmd ta_hydrology 0 \
 -ELEVATION=\"dtm_nosinks.tif\" \
 -FLOW=\"flow_accumulation.tif\" \
 -METHOD=\"Multiple Flow Direction\"

# _____________________________________
# [SAGA Topographic Wetness Index]
saga_cmd ta_hydrology 15 \
 -DEM=\"dtm_nosinks.tif\" \
 -TWI=\"saga_twi.tif\"

# _____________________________________
# [Channel Network and Drainage Basins]
saga_cmd ta_channels 5 \
 -DEM=\"dtm_nosinks.tif\" \
 -SEGMENTS=\"channels.geojson\" \
 -BASINS=\"basins.geojson\" \
 -THRESHOLD=5 -SUBBASINS=0

# _____________________________________
# #####################################

echo _____
echo finished processing!
