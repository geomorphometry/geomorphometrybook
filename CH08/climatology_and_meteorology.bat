@ECHO OFF

REM ################################################################################
REM MIT License

REM Copyright (c) 2026 J.Boehner & O.Conrad

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

REM This script supplements the chapter
REM "Land-surface parameters in climatology and meteorology"
REM written by J.Boehner, Oleg Antonic, Shabeh ul Hasson
REM (doi:10.1016/B978-0-44-333376-7.00018-5) from the text book
REM "Geomorphometry: Concepts, Software, Applications"
REM edited by Hannes I. Reuter, Carlos H. Grohmann, Vincent Lecours.
REM 
REM In order to run the script, you need to provide a recent SAGA installation
REM (https://saga-gis.org).

REM ##############################################################################

ECHO Land-surface parameters in climatology and meteorology
ECHO.

REM _____________________________________
REM #####################################
REM Configuration and Initialization

REM Select the SAGA CMD instance, that you want to use for processing:
SET SAGA_CMD="C:\saga-9.12.0_x64\saga_cmd.exe"

REM Uncomment the following line to suppress processing message output:
REM SET SAGA_CMD=%SAGA_CMD% -f=s

REM Initial Working Directory
PUSHD %~dp0

REM #____________________________________
REM Check input DEMs are available

SET dem_island="%CD%\dtm_05m_ponui_island.tif"
IF NOT EXIST %dem_island% (
    ECHO input file "%dem_island%" does not exist!
    EXIT
)

SET dem_basin="%CD%\dtm_05m_ponui_basin.tif"
IF NOT EXIST %dem_basin% (
    REM Tool: Clip Grids
    %SAGA_CMD% grid_tools 31 -GRIDS=%dem_island% -CLIPPED=%dem_basin% -XMIN=1793351 -XMAX=1795166 -YMIN=5916484 -YMAX=5917854
    IF NOT EXIST %dem_basin% (
        ECHO input file "%dem_basin%" does not exist!
        EXIT
    )
)

SET dem_nz="%CD%\SRTM (CGIAR CSI) New Zealand (1000m).tif"
IF NOT EXIST %dem_nz% (
    ECHO downloading SRTM-CGIAR DEM for New Zealand
    REM Tool: SRTM (CGIAR CSI)
    %SAGA_CMD% io_webservices 1 -RESULT=%dem_nz% ^
        -XMIN=18529000 -XMAX=19879000 -YMIN=-5264000 -YMAX=-3827000 -CELLSIZE=1000 ^
        -CRS_STRING="+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs +type=crs"
    REM targeted CRS is 'Equidistant Cylindrical' (aka 'Plate Carree')
    IF NOT EXIST %dem_nz% (
        ECHO failed to download "%dem_basin%" from SRTM CGIAR server!
        EXIT
    )
)

REM _____________________________________
REM #####################################
REM Processing

REM _____________________________________
SET dir_work="results"
IF NOT EXIST %dir_work% MKDIR %dir_work%
PUSHD %dir_work%

REM _____________________________________
REM #####################################
REM Process_Fig3(dem):
REM [Basin]
REM Fig.3: Topographic direct solar radiation on June 21 (austral winter solstice) at 02, 03, and 04 pm
REM upper row: cast-shadowing included—lower row: cast-shadowing ignored

ECHO Processing: Topographic direct solar radiation

REM Tool: Potential Incoming Solar Radiation

%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_basin% -DAY="2026-06-21" -PERIOD="moment" -MOMENT=14 -GRD_DIRECT="insolation_direct_2026-06-21_1400.tif"
%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_basin% -DAY="2026-06-21" -PERIOD="moment" -MOMENT=15 -GRD_DIRECT="insolation_direct_2026-06-21_1500.tif"
%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_basin% -DAY="2026-06-21" -PERIOD="moment" -MOMENT=16 -GRD_DIRECT="insolation_direct_2026-06-21_1600.tif"

%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_basin% -DAY="2026-06-21" -PERIOD="moment" -MOMENT=14 -GRD_DIRECT="insolation_direct_2026-06-21_1400_no-shadow.tif" -SHADOW="none"
%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_basin% -DAY="2026-06-21" -PERIOD="moment" -MOMENT=15 -GRD_DIRECT="insolation_direct_2026-06-21_1500_no-shadow.tif" -SHADOW="none"
%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_basin% -DAY="2026-06-21" -PERIOD="moment" -MOMENT=16 -GRD_DIRECT="insolation_direct_2026-06-21_1600_no-shadow.tif" -SHADOW="none"

REM _____________________________________
REM #####################################
REM [Basin]
REM Fig.4: Topographic shortwave radiation on June 21 (austral winter solstice) at 04 pm
REM (a) Topographic direct solar radiation, (b) Topographic diffuse solar radiation, (c) Topographic land surface radiation

ECHO Processing: Topographic shortwave radiation on June 21 (austral winter solstice) at 4 pm

REM Tool: Sky View Factor
%SAGA_CMD% ta_lighting 3 -DEM=%dem_basin% -SVF="svf_basin.tif"

SET atmospheric_transmittance=60

REM Tool: Potential Incoming Solar Radiation
%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_basin% -GRD_SVF="svf_basin.tif" -DAY="2026-06-21" -PERIOD="moment" -MOMENT=16 -LUMPED=%atmospheric_transmittance% ^
    -GRD_DIRECT="insolation_direct_2026-06-21_1600.tif" ^
    -GRD_DIFFUS="insolation_diffuse_2026-06-21_1600.tif" ^
    -GRD_TOTAL="insolation_total_2026-06-21_1600.tif"

REM _____________________________________
REM #####################################
REM [Ponui Island]
REM Fig.5: Spatial distribution of potential topographic net shortwave radiation for Ponui Island
REM (a) 21 December (austral summer solstice), (b) 21 June (austral winter solstice).

ECHO Processing: Spatial distribution of potential topographic net shortwave radiation for Ponui Island

REM Tool: Sky View Factor
%SAGA_CMD% ta_lighting 3 -DEM=%dem_island% -SVF="svf_island.tif" -RADIUS=1000

REM Tool: Potential Incoming Solar Radiation
%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_island% -GRD_SVF="svf_island.tif" -DAY="2026-12-21" -PERIOD="day" -LUMPED=%atmospheric_transmittance% ^
    -GRD_TOTAL="net_shortwave_radiation_2026-12-21_kWh_m2.tif"

%SAGA_CMD% ta_lighting 2 -GRD_DEM=%dem_island% -GRD_SVF="svf_island.tif" -DAY="2026-06-21" -PERIOD="day" -LUMPED=%atmospheric_transmittance% ^
    -GRD_TOTAL="net_shortwave_radiation_2026-06-21_kWh_m2.tif"

REM Tool: Grid Multiplication | [kWh/m2] >> [W/m2] | 1000 / 24 = 41.66666667
%SAGA_CMD% grid_calculus 23 -A="net_shortwave_radiation_2026-12-21_kWh_m2.tif" -C="net_shortwave_radiation_2026-12-21.tif" -B_DEFAULT=41.66666667
%SAGA_CMD% grid_calculus 23 -A="net_shortwave_radiation_2026-06-21_kWh_m2.tif" -C="net_shortwave_radiation_2026-06-21.tif" -B_DEFAULT=41.66666667

REM _____________________________________
REM #####################################
REM [New Zealand]
REM Fig.7: Topography vs. temperature distribution in New Zealand-Topography (a)
REM and spatial distribution of mean daily temperature in January (b) and July (c),
REM 1981-2010 long-term means (Karger et al., 2017).

ECHO Processing: Topography vs. temperature distribution in New Zealand-Topography

REM Tool: CHELSA - Global Climate Data
%SAGA_CMD% io_webservices 15 -MEMTYPE="single grids" -GRIDS="nz_chelsa_tmean_1981-2010_.tif" ^
    -DATASET="climatology" -PERIOD="1981-2010" -VAR_CLIMATE="Daily Mean Near-Surface Air Temperature" ^
    -EXTENT="grid system" -GRID=%dem_nz%

REM Tool: Grid Masking
%SAGA_CMD% grid_tools 24 -MASK=%dem_nz% -GRID="nz_chelsa_tmean_1981-2010_01.tif" -MASKED="nz_chelsa_tmean_1981-2010_jan.tif"
%SAGA_CMD% grid_tools 24 -MASK=%dem_nz% -GRID="nz_chelsa_tmean_1981-2010_07.tif" -MASKED="nz_chelsa_tmean_1981-2010_jul.tif"

REM _____________________________________
REM #####################################
REM [New Zealand]
REM Fig.8: Topography vs. vapour pressure distribution in New Zealand-Topography (a),
REM and spatial distribution of mean daily vapour pressure in January (b) and July (c),
REM 1981-2010 long-term means (Karger et al., 2017).

ECHO Processing: Topography vs. vapour pressure distribution in New Zealand-Topography

REM Tool: CHELSA - Global Climate Data
%SAGA_CMD% io_webservices 15 -MEMTYPE="single grids" -GRIDS="nz_chelsa_rh_1981-2010_.tif" ^
    -DATASET="climatology" -PERIOD="1981-2010" -VAR_CLIMATE="Near-Surface Relative Humidity" ^
    -EXTENT="grid system" -GRID=%dem_nz%

REM Tool: Grid Masking
%SAGA_CMD% grid_tools 24 -MASK=%dem_nz% -GRID="nz_chelsa_rh_1981-2010_01.tif" -MASKED="nz_chelsa_rh_1981-2010_jan.tif"
%SAGA_CMD% grid_tools 24 -MASK=%dem_nz% -GRID="nz_chelsa_rh_1981-2010_07.tif" -MASKED="nz_chelsa_rh_1981-2010_jul.tif"

REM Air Humidity Conversions
%SAGA_CMD% climate_tools 29 -CONVERSION=2 -IN_RH="nz_chelsa_rh_1981-2010_jan.tif" -T="nz_chelsa_tmean_1981-2010_jan.tif" -OUT_VP="nz_chelsa_vp_1981-2010_jan.tif"
%SAGA_CMD% climate_tools 29 -CONVERSION=2 -IN_RH="nz_chelsa_rh_1981-2010_jul.tif" -T="nz_chelsa_tmean_1981-2010_jul.tif" -OUT_VP="nz_chelsa_vp_1981-2010_jul.tif"

REM _____________________________________
REM #####################################
REM [Basin]
REM Fig.9: Land Surface Parameters effecting temperature and moisture distribution
REM (a) diurnal anisotropic heating (αmax = 202.5°), (b) relative slope position, and (c) delineated relative vertical distance to mid-slope position.

ECHO Processing: Land Surface Parameters effecting temperature and moisture distribution

REM Tool: Diurnal Anisotropic Heat
%SAGA_CMD% ta_morphometry 12 -DEM=%dem_basin% -ALPHA_MAX=202.5 -DAH="diurnal_anisotropic_heating.tif"

REM Tool: Relative Heights and Slope Positions
%SAGA_CMD% ta_morphometry 14 -DEM=%dem_basin% -NH="relative_slope_position.tif" -MS="mid_slope_position.tif"

REM _____________________________________
REM #####################################
REM [Ponui Island]
REM Fig.10: Wind Exposition Index (WEI) for wind direction southwest (a)
REM and averaged over the full circle at an angle increment of 15° (b).

ECHO Processing: Wind Exposition Index

REM Tool: Wind Effect (Windward / Leeward Index)
REM wind is blowing from SW (225°), but tool wants direction to which the wind blows (225°-180°=45°)!
%SAGA_CMD% ta_morphometry 15 -DEM=%dem_island% -DIR_CONST=45 -EFFECT="wei_from_southwest.tif"

REM Tool: Wind Exposition Index
%SAGA_CMD% ta_morphometry 27 -DEM=%dem_island% -STEP=15 -EXPOSITION="wei_full.tif"

REM _____________________________________
REM #####################################
REM [New Zealand]
REM Fig.11: Topographic exposure vs. precipitation distribution in New Zealand
REM Windward-Leeward Index (WLI) for advection direction west (a) and spatial distribution of mean monthly precipitation in January (b) and July (c),
REM 1981-2010 long-term means (Karger et al., 2017).

ECHO Processing: Topographic exposure vs. precipitation distribution in New Zealand

REM Tool: Wind Effect (Windward / Leeward Index)
REM wind is blowing from W (270°), but tool wants direction to which the wind blows (270°-180°=90°)!
%SAGA_CMD% ta_morphometry 15 -DEM=%dem_island% -DIR_CONST=90 -EFFECT="nz_wei_from_west.tif"

REM Tool: CHELSA - Global Climate Data
%SAGA_CMD% io_webservices 15 -MEMTYPE="single grids" -GRIDS="nz_chelsa_p_1981-2010_.tif" ^
    -DATASET="climatology" -PERIOD="1981-2010" -VAR_CLIMATE="Precipitation" ^
    -EXTENT="grid system" -GRID=%dem_nz%

REM Tool: Grid Masking
%SAGA_CMD% grid_tools 24 -MASK=%dem_nz% -GRID="nz_chelsa_p_1981-2010_01.tif" -MASKED="nz_chelsa_p_1981-2010_jan.tif"
%SAGA_CMD% grid_tools 24 -MASK=%dem_nz% -GRID="nz_chelsa_p_1981-2010_07.tif" -MASKED="nz_chelsa_p_1981-2010_jul.tif"

REM _____________________________________
REM #####################################

ECHO _____
ECHO finished processing!

PAUSE
