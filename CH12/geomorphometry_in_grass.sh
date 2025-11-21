#!/bin/bash

# Define variables
PROJECT_NAME = "ponui"
MAPSET_NAME = "PERMANENT"

DSM_PATH="/path/to/dsm.tif"
DSM_NAME="dsm"
DTM_PATH="/path/to/dem.tif"
DTM_NAME="dem"
LIDAR_PATH="/path/to/lidar.laz"
LIDAR_NAME="lidar"
SAVE_DIR="figures"

# Create a new GRASS GIS project with EPSG:2193
grass -c EPSG:2193 $PROJECT_NAME

# Import the DSM GeoTIFF into the GRASS project with bilinear resampling
r.import input="$DSM_PATH" output="$DSM_NAME" resample=bilinear
r.import input="$DTM_PATH" output="$DTM_NAME" resample=bilinear

g.region -pa raster="$DTM_NAME" res=1

# Apply the color scheme
r.colors map=$DSM_NAME,$DTM_NAME color=elevation

for res in 100 200 300; do
    g.region -pa raster="$DTM_NAME" res="$res"
    r.resamp.interp input="$DTM_NAME" output="dtm_${res}m" method=bilinear
done

g.region -a raster="$DTM_NAME" res=1
r.slope.aspect elevation="$DTM_NAME" slope=slope aspect=aspect pcurvature=pcurv tcurvature=tcurv dx=dx dy=dy
r.colors map=slope color=sepia -e
r.colors map=aspect color=aspectcolr -e

# Calculate downslope flowlines
r.flow elevation=dtm flowline=flowlines flowlength=flowlength flowaccumulation=flowaccum

# Delineate watersheds, flow direction, and streams
r.watershed elevation=dtm threshold=10000 accumulation=flowaccum drainage=flow_direction basin=basins stream=streams

