@ECHO OFF

REM ################################################################################
REM MIT License

REM Copyright (c) 2024 Olaf Conrad, Volker Wichmann

REM Permission is hereby granted, free of charge, to any person obtaining a copy
REM of this software and associated documentation files (the "Software"), to deal
REM in the Software without restriction, including without limitation the rights
REM to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
REM copies of the Software, and to permit persons to whom the Software is
REM furnished to do so, subject to the following conditions:

REM The above copyright notice and this permission notice shall be included in all
REM copies or substantial portions of the Software.

REM THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
REM IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
REM FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
REM AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
REM LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
REM OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
REM SOFTWARE.
REM ##############################################################################


REM ##############################################################################
 
REM  This script supplements the chapter "Geomorphometry in SAGA" from the
REM  Geomorphometry book and generates the data sets presented there for
REM  Ponui Island. This script has been worked out with SAGA 9.7.
 
REM  In order to run the script, the paths to "saga_cmd" and the input LAS file
REM  must be adjusted in the "Configuration" section.

REM  The script performs the following calculations: (i) DEM creation from the
REM  point cloud, (ii) contour line calculation, (iii) morphometric analysis,
REM  (iv) relief classification and (v) hydological analysis.

REM ##############################################################################

REM _____________________________________
REM #####################################
REM Configuration

REM Select the SAGA CMD instance, that you want to use for processing.
SET SAGA_CMD=C:\saga-9.7.0_x64\saga_cmd.exe

REM Where is the point cloud file to be processed?
SET FILE_LAS=C:\Ponui Island\ponui.laz

REM Set CRS, target cellsize, file names and formats (raster: tif/sg-grd-z, vector: shp/gpkg/geojson').
SET CRS=epsg:2193
SET CELLSIZE=5
SET FILE_DSM=dsm_%CELLSIZE%m
SET FILE_DTM=dtm_%CELLSIZE%m
SET FMT_RASTER=tif
SET FMT_VECTOR=geojson

REM Choose a directory for storing the results.
SET WORKDIR=%~dp0\results_%CELLSIZE%m
IF NOT EXIST "%WORKDIR%" MKDIR "%WORKDIR%"
PUSHD "%WORKDIR%"

REM _____________________________________
REM #####################################
REM Digital Surface Model (Ground, Buildings, Vegetation)

REM _____________________________________
REM [Import Grid from Point Cloud]
REM Use all valid points (ground, buildings, low/mid/high vegetation: classes = 2, 3, 4, 5, 6).
REM Request maximum value if more than one point falls into a target cell (aggregation).
REM Set target cellsize, target extent will be fitted to the points data.
%SAGA_CMD% io_pdal 2 ^
 -FILES="%FILE_LAS%" ^
 -CLASSES="2,3,4,5,6" ^
 -AGGREGATION="maximum" ^
 -TARGET_DEFINITION="user defined" ^
 -TARGET_USER_SIZE=%CELLSIZE% ^
 -GRID="%FILE_DSM%.%FMT_RASTER%"

REM _____________________________________
REM [Set Coordinate Reference System]
REM LAS file does not know about its CRS ...but we do!
%SAGA_CMD% pj_proj4 0 ^
 -CRS_STRING="%CRS%" ^
 -GRIDS="%FILE_DSM%.%FMT_RASTER%" ^
 -GRIDS_OUT="%FILE_DSM%.%FMT_RASTER%"

REM _____________________________________
REM [Shrink and Expand]
REM Closing gaps, result overwrites input raster.
%SAGA_CMD% grid_tools 28 ^
 -INPUT="%FILE_DSM%.%FMT_RASTER%" ^
 -RESULT="%FILE_DSM%.%FMT_RASTER%" ^
 -OPERATION="expand and shrink" ^
 -RADIUS=6 ^
 -EXPAND="maximum"

REM _____________________________________
REM #####################################
REM Digital Terrain Model (Ground)

REM _____________________________________
REM [Import Grid from Point Cloud]
REM Use ground points only (class = 2).
REM Request mean value if more than one point falls into a target cell (aggregation).
REM Take the same grid system as used by the surface model (target template = DSM).
%SAGA_CMD% io_pdal 2 ^
 -FILES="%FILE_LAS%" ^
 -CLASSES="2" ^
 -AGGREGATION="mean" ^
 -TARGET_DEFINITION="grid or grid system" ^
 -TARGET_TEMPLATE="%FILE_DSM%.%FMT_RASTER%" ^
 -GRID="%FILE_DTM%.%FMT_RASTER%"

REM _____________________________________
REM [Set Coordinate Reference System]
REM LAS file does not know about its CRS ...but we do!
%SAGA_CMD% pj_proj4 0 ^
 -CRS_STRING="%CRS%" ^
 -GRIDS="%FILE_DTM%.%FMT_RASTER%" ^
 -GRIDS_OUT="%FILE_DTM%.%FMT_RASTER%"

REM _____________________________________
REM [Multilevel B-Spline from Grid Points]
REM Create a DEM free of gaps using spline interpolation.
%SAGA_CMD% grid_spline 5 ^
 -TARGET_DEFINITION="grid or grid system" ^
 -TARGET_TEMPLATE="%FILE_DTM%.%FMT_RASTER%" ^
 -TARGET_OUT_GRID="%FILE_DTM%_splined.%FMT_RASTER%" ^
 -GRID="%FILE_DTM%.%FMT_RASTER%"

REM _____________________________________
REM [Grid Masking]
REM Apply the DSM as land mask.
%SAGA_CMD% grid_tools 24 ^
 -GRID="%FILE_DTM%_splined.%FMT_RASTER%" ^
 -MASKED="%FILE_DTM%_splined.%FMT_RASTER%" ^
 -MASK="%FILE_DSM%.%FMT_RASTER%"

REM _____________________________________
REM [Patching]
REM Fill any gaps with interpolated values.
%SAGA_CMD% grid_tools 5 ^
 -ORIGINAL="%FILE_DTM%.%FMT_RASTER%" ^
 -COMPLETED="%FILE_DTM%.%FMT_RASTER%" ^
 -ADDITIONAL="%FILE_DTM%_splined.%FMT_RASTER%" ^
 -RESAMPLING=3

REM _____________________________________
REM [Grid Calculator]
REM Calculate the difference between DSM and DTM.
%SAGA_CMD% grid_calculus 1 ^
 -FORMULA="g1 - g2" ^
 -GRIDS="%FILE_DSM%.%FMT_RASTER%; %FILE_DTM%.%FMT_RASTER%" ^
 -RESULT="%FILE_DSM% Height above Ground.%FMT_RASTER%"

REM _____________________________________
REM #####################################
REM Contour Lines

REM _____________________________________
REM [Countour Lines from Grid]
SET INTERVAL=10
%SAGA_CMD% shapes_grid 5 ^
 -GRID="%FILE_DTM%.%FMT_RASTER%" ^
 -CONTOUR="%FILE_DTM% %INTERVAL%m Contours.%FMT_VECTOR%" ^
 -ZSTEP=%INTERVAL% 

REM _____________________________________
REM [Countour Lines from Grid]
SET INTERVAL=50
%SAGA_CMD% shapes_grid 5 ^
 -GRID="%FILE_DTM%.%FMT_RASTER%" ^
 -CONTOUR="%FILE_DTM% %INTERVAL%m Contours.%FMT_VECTOR%" ^
 -ZSTEP=%INTERVAL% 

REM _____________________________________
REM #####################################
REM Examples: Morphometry

REM _____________________________________
REM [Analytical Hillshading]
%SAGA_CMD% ta_lighting 0 ^
 -ELEVATION="%FILE_DTM%.%FMT_RASTER%" ^
 -SHADE="%FILE_DTM% Shading.%FMT_RASTER%" ^
 -AZIMUTH=315 -DECLINATION=45 -EXAGGERATION=1

REM _____________________________________
REM [Slope, Aspect, Curvature]
%SAGA_CMD% ta_morphometry 0 ^
 -ELEVATION="%FILE_DTM%.%FMT_RASTER%" ^
 -SLOPE="%FILE_DTM% Slope.%FMT_RASTER%" ^
 -ASPECT="%FILE_DTM% Aspect.%FMT_RASTER%" ^
 -C_PROF="%FILE_DTM% Profile Curvature.%FMT_RASTER%" ^
 -C_PLAN="%FILE_DTM% Plan Curvature.%FMT_RASTER%" ^
 -METHOD="9 parameter 2nd order polynom (Zevenbergen & Thorne 1987)" ^
 -UNIT_SLOPE="degree" -UNIT_ASPECT="degree"

REM _____________________________________
REM [Topographic Position Index]
%SAGA_CMD% ta_morphometry 18 ^
 -DEM="%FILE_DTM%.%FMT_RASTER%" ^
 -TPI="%FILE_DTM% Topographic Position Index.%FMT_RASTER%"

REM _____________________________________
REM [Topographic Openness]
%SAGA_CMD% ta_lighting 5 ^
 -DEM="%FILE_DTM%.%FMT_RASTER%" ^
 -POS="%FILE_DTM% Positive Openness.%FMT_RASTER%" ^
 -NEG="%FILE_DTM% Negative Openness.%FMT_RASTER%"

REM _____________________________________
REM #####################################
REM Examples: Relief Classification

REM _____________________________________
REM [Curvature Classification]
%SAGA_CMD% ta_morphometry 4 ^
 -DEM="%FILE_DTM%.%FMT_RASTER%" ^
 -CLASSES="%FILE_DTM% Classes - Curvature Classification.%FMT_RASTER%" ^
 -STRAIGHT=175.0 -SMOOTH=10

REM _____________________________________
REM [Geomorphons]
%SAGA_CMD% ta_lighting 8 ^
 -DEM="%FILE_DTM%.%FMT_RASTER%" ^
 -GEOMORPHONS="%FILE_DTM% Classes - Geomorphons.%FMT_RASTER%" ^
 -THRESHOLD=1.0 -RADIUS=150.0

REM _____________________________________
REM [TPI Based Landform Classification]
%SAGA_CMD% ta_morphometry 19 ^
 -DEM="%FILE_DTM%.%FMT_RASTER%" ^
 -LANDFORMS="%FILE_DTM% Classes - Landforms.%FMT_RASTER%" ^
 -RADIUS_A_MAX=25.0 ^
 -RADIUS_B_MAX=150.0

REM _____________________________________
REM [Morphometric Features]
%SAGA_CMD% ta_morphometry 23 ^
 -DEM="%FILE_DTM%.%FMT_RASTER%" ^
 -FEATURES="%FILE_DTM% Classes - Morphometric Features.%FMT_RASTER%" ^
 -SIZE=10 -TOL_SLOPE=10.0 -TOL_CURVE=0.005 -EXPONENT=0 -ZSCALE=1 -CONSTRAIN=1

REM _____________________________________
REM #####################################
REM Examples: Hydrology

SET FILE_DTM_NOSINKS=%FILE_DTM% [no sinks].%FMT_RASTER%

REM _____________________________________
REM [Fill Sinks (Wang & Liu)]
%SAGA_CMD% ta_preprocessor 5 ^
 -ELEV="%FILE_DTM%.%FMT_RASTER%" ^
 -FILLED="%FILE_DTM_NOSINKS%.%FMT_RASTER%" ^
 -MINSLOPE=0.1

REM _____________________________________
REM [Flow Accumulation (Top-Down)]
%SAGA_CMD% ta_hydrology 0 ^
 -ELEVATION="%FILE_DTM_NOSINKS%.%FMT_RASTER%" ^
 -FLOW="%FILE_DTM% Flow Accumulation.%FMT_RASTER%" ^
 -METHOD="Multiple Flow Direction"

REM _____________________________________
REM [SAGA Topographic Wetness Index]
%SAGA_CMD% ta_hydrology 15 ^
 -DEM="%FILE_DTM_NOSINKS%.%FMT_RASTER%" ^
 -TWI="%FILE_DTM% SAGA TWI.%FMT_RASTER%"

REM _____________________________________
REM [Channel Network and Drainage Basins]
%SAGA_CMD% ta_channels 5 ^
 -DEM="%FILE_DTM_NOSINKS%.%FMT_RASTER%" ^
 -SEGMENTS="%FILE_DTM% Channels.%FMT_VECTOR%" ^
 -BASINS="%FILE_DTM% Drainage Basins.%FMT_VECTOR%" ^
 -THRESHOLD=5 -SUBBASINS=0

REM _____________________________________
REM #####################################

ECHO _____
ECHO finished processing!

PAUSE
