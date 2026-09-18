#!/bin/bash

# Run this script from the CH19 directory.
#
# 1. Download the required data from Zenodo.
# 2. Place the downloaded files in the Data directory.
# 3. Navigate to the CH19 directory:
#
#      cd "/path/to/CH19"
#
# 4. Run:
#
#      bash prepare_data.sh

# Extract ZIP archives
unzip "Data/LAS_ponui_island_lidar_las.zip" -d "Data"
unzip "Data/LAS_ponui_island_lidar.zip" -d "Data"
unzip "Data/VECT_ponui_buffer_10m.zip" -d "Data"

# Rename files to match the filenames used in the chapter
mv "Data/LAS_ponui_island_lidar.las" "Data/ponui.las"
mv "Data/LAS_ponui_island_lidar.laz" "Data/ponui.laz"
mv "Data/ponui_buffer_10m.gpkg" "Data/ponui_buffer10m.gpkg"
mv "Data/DEM_ponui_island_dsm.tif" "Data/ponui_island_dsm.tif"
mv "Data/DEM_ponui_island_dtm.tif" "Data/ponui_island_dtm.tif"

echo "Data preparation complete."