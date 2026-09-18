@echo off

REM ----------------------------------------------------------
REM Prepare data files for the chapter examples
REM ----------------------------------------------------------
REM
REM 1. Download the required data from Zenodo.
REM 2. Place all downloaded files in the Data directory.
REM 3. Open Command Prompt and navigate to the CH19 directory.
REM
REM Example:
REM   cd /d "C:\path\to\CH19"
REM
REM 4. Run:
REM   prepare_data.cmd
REM ----------------------------------------------------------

REM Extract ZIP archives
tar -xf "Data\LAS_ponui_island_lidar.zip" -C "Data"
tar -xf "Data\LAS_ponui_island_lidar_las.zip" -C "Data"
tar -xf "Data\VECT_ponui_buffer_10m.zip" -C "Data"

REM Rename extracted files to match filenames used in the chapter
ren "Data\LAS_ponui_island_lidar.las" "ponui.las"
ren "Data\LAS_ponui_island_lidar.laz" "ponui.laz"
ren "Data\ponui_buffer_10m.gpkg" "ponui_buffer10m.gpkg"

REM Rename directly downloaded raster files
ren "Data\DEM_ponui_island_dsm.tif" "ponui_island_dsm.tif"
ren "Data\DEM_ponui_island_dtm.tif" "ponui_island_dtm.tif"

echo.
echo Data preparation complete.
pause