@echo off

REM Run this script from the CH19 directory.
REM
REM This script downloads the data required for the chapter examples
REM from Zenodo and places the files in the Data directory.
REM
REM Navigate to the CH19 directory:
REM
REM     cd /d "C:\path\to\CH19"
REM
REM Then run:
REM
REM     download_data.cmd

REM Create Data directory if it does not already exist
if not exist "Data" mkdir "Data"

REM Primary Zenodo dataset:
REM https://doi.org/10.5281/zenodo.18314107

curl -L "https://zenodo.org/records/18314107/files/LAS_ponui_island_lidar.zip?download=1" ^
     -o "Data\LAS_ponui_island_lidar.zip"

curl -L "https://zenodo.org/records/18314107/files/VECT_ponui_buffer_10m.zip?download=1" ^
     -o "Data\VECT_ponui_buffer_10m.zip"

curl -L "https://zenodo.org/records/18314107/files/DEM_ponui_island_dsm.tif?download=1" ^
     -o "Data\DEM_ponui_island_dsm.tif"

curl -L "https://zenodo.org/records/18314107/files/DEM_ponui_island_dtm.tif?download=1" ^
     -o "Data\DEM_ponui_island_dtm.tif"

REM LAS dataset:
REM https://doi.org/10.5281/zenodo.22769771

curl -L "https://zenodo.org/records/22769771/files/LAS_ponui_island_lidar_las.zip?download=1" ^
     -o "Data\LAS_ponui_island_lidar_las.zip"

echo.
echo Data download complete.
pause