#!/usr/bin/env bash

# Geomorphometry in GRASS (Chapter 12) - CLI workflow
#
# Notes:
# - This script is intentionally simple and does not generate figures/maps.
# - It assumes you have GRASS 8.5+ installed and available as `grass`.
# - GRASS add-ons are NOT installed automatically here (see section below).
#   This avoids failures on systems where `g.extension` is broken/mismatched.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# --- GRASS project settings ---
PROJECT_NAME="ponui"
MAPSET_NAME="PERMANENT"
EPSG_CODE="2193"
GISDBASE="$PROJECT_DIR"
PROJECT_PATH="$GISDBASE/$PROJECT_NAME"

# --- Input data (Remote files by default) ---
DSM_TIF="/vsicurl/https://zenodo.org/records/18314107/files/DEM_ponui_island_dsm.tif?download=1"
DTM_TIF="/vsicurl/https://zenodo.org/records/18314107/files/DEM_ponui_island_dtm.tif?download=1"

# --- Input data (local files) ---
# DSM_TIF="$PROJECT_DIR/data/dsm.cog.tif"
# DTM_TIF="$PROJECT_DIR/data/dtm.cog.tif"
LIDAR_LAZ="$PROJECT_DIR/data/LAS_ponui_island_lidar.laz"

# --- Raster names used in the chapter workflow ---
DSM_NAME="dsm_10m"
DTM_NAME="dem_10m"
DTM_RELIEF="dtm_relief"

LIDAR_DTM_10M="lidar_dtm_10m"
LIDAR_DTM_1M="lidar_dtm_1m"
LIDAR_DTM_1M_RELIEF="lidar_dtm_1m_relief"
LIDAR_DTM_1M_SKYVIEW="lidar_dtm_1m_skyview"

AOI_REGION="aoi"
AOI_RES="1"

ISLAND_RES="10"

# Set a custom number of cores to use here or
# all available cores will be set by default.
NPROCS=""

AVAILABLE_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)

: "${NPROCS:=$AVAILABLE_CORES}"

if [[ ! "$NPROCS" =~ ^[0-9]+$ ]] || (( NPROCS < 1 )); then
    echo "Warning: Invalid NPROCS ('$NPROCS'). Falling back to $AVAILABLE_CORES cores." >&2
    NPROCS=$AVAILABLE_CORES
fi

require_file() {
	local path="$1"
	if [[ ! -f "$path" ]]; then
		echo "ERROR: Missing file: $path" >&2
		exit 1
	fi
}

have_module() {
	command -v "$1" >/dev/null 2>&1
}

warn_missing_addon() {
	local mod="$1"
	echo "WARNING: GRASS module '$mod' not found; skipping related step." >&2
	echo "         Install add-ons listed in CH12/gextensions.txt if needed." >&2
}

if [[ -z "${GISRC:-}" && "${IN_GRASS_EXEC:-}" != "1" ]]; then
	# Outside GRASS: create project if needed, then re-exec inside GRASS.
	require_file "$DSM_TIF"
	require_file "$DTM_TIF"
	require_file "$LIDAR_LAZ"

	if [[ ! -d "$PROJECT_PATH" ]]; then
		echo "Creating GRASS project at: $PROJECT_PATH (EPSG:$EPSG_CODE)"
		grass -c "EPSG:$EPSG_CODE" -e "$PROJECT_PATH" >/dev/null
	fi

	export IN_GRASS_EXEC=1
	exec grass "$PROJECT_PATH/$MAPSET_NAME" --exec "$0" "$@"
fi

echo "Running inside GRASS session."
g.gisenv

# Allow the workflow to be re-run against an existing project.
export GRASS_OVERWRITE=1

# Ensure the basin mask never survives a crash into future sessions.
trap 'r.mask -r --quiet 2>/dev/null || true' EXIT

# -----------------------------------------------------------------------------
# Add-ons (manual install)
# -----------------------------------------------------------------------------
# This workflow uses several add-ons (see CH12/gextensions.txt), e.g.:
# - r.skyview, r.hand, r.flowaccumulation, r.tpi, r.stream.order
#
# If your `g.extension` is working, you can install them once via:
#   grass "$PROJECT_PATH/$MAPSET_NAME" --exec g.extension extension=r.hand
#
# If `g.extension` is broken on your machine (e.g. RuntimePaths.is_cmake_build),
# fix your GRASS installation consistency first, or install add-ons via your
# system packages.

# -----------------------------------------------------------------------------
# 1) Import base rasters + 10m LiDAR mean DTM
# -----------------------------------------------------------------------------
echo "Importing DSM/DTM ($ISLAND_RES m) and LiDAR mean DTM..."

r.import input="$DSM_TIF" output="$DSM_NAME" \
	resample=bilinear resolution=value resolution_value="$ISLAND_RES" \
	title="Ponui Island ${ISLAND_RES}m DSM" --quiet

r.import input="$DTM_TIF" output="$DTM_NAME" \
	resample=bilinear resolution=value resolution_value="$ISLAND_RES" \
	title="Ponui Island ${ISLAND_RES}m DTM" --quiet

# LiDAR mean raster at island resolution
r.in.pdal input="$LIDAR_LAZ" output="$LIDAR_DTM_10M" \
	method=mean resolution="$ISLAND_RES" class_filter=2 -we --quiet

# Set ocean values (< 0) to NULL
r.null map="$DTM_NAME" setnull="-9999-0" --quiet
r.null map="$DSM_NAME" setnull="-9999-0" --quiet
r.null map="$LIDAR_DTM_10M" setnull="-9999-0" --quiet

# Region to island DTM
g.region raster="$DTM_NAME" -a

echo "Computing relief (island)..."
r.relief input="$DTM_NAME" output="$DTM_RELIEF" --quiet

echo "Computing 2nd order derivatives (island)..."
r.slope.aspect elevation="$DTM_NAME" \
	slope="${DTM_NAME}_slope" aspect="${DTM_NAME}_aspect" \
	pcurvature="${DTM_NAME}_pcurv" tcurvature="${DTM_NAME}_tcurv" \
	dx="${DTM_NAME}_dx" dy="${DTM_NAME}_dy" --quiet

# Resample to coarser resolutions (analysis outputs only)
for res in 150 250 500; do
	echo "Resampling $DTM_NAME to ${res}m..."
	g.region res="$res" raster="$DTM_NAME"
	r.resamp.interp input="$DTM_NAME" output="${DTM_NAME}_${res}m" method=bilinear --quiet
done

# -----------------------------------------------------------------------------
# 2) AOI: region, LiDAR processing, interpolation, derivatives
# -----------------------------------------------------------------------------
echo "Setting AOI region (${AOI_RES}m)..."
g.region \
	n=5918600.13 s=5917599.13 w=1793519.48 e=1794520.48 \
	res="$AOI_RES" -ap
g.region save="$AOI_REGION"

# AOI boundary vector (useful for debugging and optional masking)
v.in.region output="$AOI_REGION" type=area --quiet

g.region region="$AOI_REGION" res="$AOI_RES" -a

echo "Importing LiDAR ground points (vector)..."
v.in.pdal input="$LIDAR_LAZ" output="lidar_be" class_filter=2 -or --quiet

echo "Counting LiDAR points per cell (1m)..."
r.in.pdal input="$LIDAR_LAZ" output="lidar_dtm_n_1m" method=n resolution=1 class_filter=2 -we --quiet

echo "Interpolating LiDAR DTM (RST)..."
v.surf.rst input="lidar_be" elevation="$LIDAR_DTM_1M" \
	slope="${LIDAR_DTM_1M}_rst_slope" aspect="${LIDAR_DTM_1M}_rst_aspect" \
	pcurvature="${LIDAR_DTM_1M}_rst_pcurv" tcurvature="${LIDAR_DTM_1M}_rst_tcurv" \
	mcurvature="${LIDAR_DTM_1M}_rst_mcurv" \
	tension=300 smooth=0.1 npmin=200 dmin=1.5 nprocs=$NPROCS -t --quiet

r.null map="$LIDAR_DTM_1M" setnull="-9999-0" --quiet

echo "Relief + derivatives (AOI LiDAR DTM)..."
r.relief input="$LIDAR_DTM_1M" output="$LIDAR_DTM_1M_RELIEF" --quiet

r.slope.aspect elevation="$LIDAR_DTM_1M" \
	slope="${LIDAR_DTM_1M}_slope" aspect="${LIDAR_DTM_1M}_aspect" \
	pcurvature="${LIDAR_DTM_1M}_pcurv" tcurvature="${LIDAR_DTM_1M}_tcurv" \
	dx="${LIDAR_DTM_1M}_dx" dy="${LIDAR_DTM_1M}_dy" --quiet

# Optional: edge-preserving smoothing (module availability depends on build)
if have_module r.smooth.edgepreserve; then
	echo "Smoothing LiDAR DTM (edge-preserving Tukey)..."
	r.smooth.edgepreserve input="$LIDAR_DTM_1M" output="${LIDAR_DTM_1M}_s_agg_tukey" \
		function=tukey threshold=15 lambda=0.4 steps=20 --quiet

	r.slope.aspect elevation="${LIDAR_DTM_1M}_s_agg_tukey" \
		slope="${LIDAR_DTM_1M}_s_agg_tukey_slope" aspect="${LIDAR_DTM_1M}_s_agg_tukey_aspect" \
		pcurvature="${LIDAR_DTM_1M}_s_agg_tukey_pcurv" tcurvature="${LIDAR_DTM_1M}_s_agg_tukey_tcurv" \
		dx="${LIDAR_DTM_1M}_s_agg_tukey_dx" dy="${LIDAR_DTM_1M}_s_agg_tukey_dy" --quiet
else
	echo "NOTE: r.smooth.edgepreserve not found; skipping smoothing." >&2
fi

# -----------------------------------------------------------------------------
# 3) Hydrology: flow accumulation, TWI, streams, HAND
# -----------------------------------------------------------------------------
echo "Computing flow accumulation methods..."

# D8 MFD
r.watershed elevation="$LIDAR_DTM_1M" \
	accumulation="d8_mfd_flowaccum" drainage="d8_mfd_flowdir" \
	stream="d8_mfd_streams" basin="d8_mfd_basins2" \
	threshold=100000 -a4 --quiet

# D8 SFD
r.watershed elevation="$LIDAR_DTM_1M" \
	accumulation="d8_sfd_flowaccum" drainage="d8_sfd_flowdir" \
	threshold=100000 -sa --quiet

# D-infinity SFD
r.flow elevation="$LIDAR_DTM_1M" flowaccumulation="dinf_sfd_flowaccum" --quiet
r.null map="dinf_sfd_flowaccum" setnull="-9999-0" --quiet

# MEFA (add-on r.flowaccumulation)
if have_module r.flowaccumulation; then
	r.flowaccumulation input="d8_sfd_flowdir" format=45degree \
		output="MEFA_flowaccum" type=CELL --quiet
else
	warn_missing_addon r.flowaccumulation
fi

echo "Computing TWI..."
r.mapcalc "twi = log(d8_mfd_flowaccum / tan(${LIDAR_DTM_1M}_slope * 3.14159 / 180))" --quiet

echo "Delineating streams + stream order..."
if have_module r.stream.order && have_module r.stream.extract; then
	r.thin input="d8_mfd_streams" output="d8_mfd_streams_thin" --quiet
	r.to.vect input="d8_mfd_streams_thin" output="d8_mfd_streams" type=line --quiet

	r.stream.extract elevation="$LIDAR_DTM_1M" threshold=5000 \
		direction="stream_extract_dir" stream_raster="stream_extract" \
		stream_vector="stream_extract" --quiet

	r.stream.order elevation="$LIDAR_DTM_1M" accumulation="d8_mfd_flowaccum" \
		direction="stream_extract_dir" stream_rast="stream_extract" \
		stream_vect="stream_orders" strahler="strahler" horton="horton" --quiet
else
	warn_missing_addon r.stream.order
	warn_missing_addon r.stream.extract
fi

echo "Running HAND workflow..."
if have_module r.hand; then
	r.hand elevation="$LIDAR_DTM_1M" threshold=50000 \
		inundation_raster="inundation" inundation_strds="inundation_strds" \
		start_water_level=0 end_water_level=5 water_level_step=0.5 \
		hand="hand" -t --quiet
else
	warn_missing_addon r.hand
fi

# -----------------------------------------------------------------------------
# 4) Overland flow + erosion/deposition (masked to basin)
# -----------------------------------------------------------------------------
echo "Converting basins raster to vector for masking..."
r.to.vect input="d8_mfd_basins2" output="d8_mfd_basins2" type=area --quiet

echo "Masking to basin and running r.sim.water / r.sim.sediment..."
r.mask vector="d8_mfd_basins2" --quiet

r.sim.water elevation="$LIDAR_DTM_1M" dx="${LIDAR_DTM_1M}_dx" dy="${LIDAR_DTM_1M}_dy" \
	rain_value=30 infil_value=0.0 man_value=0.2 \
	niterations=30 output_step=2 \
	depth="depth" discharge="disch" \
	random_seed=3 nwalkers=100000 nprocs=$NPROCS -t

r.mapcalc "max_depth = if(depth.30 >= 0.01, depth.30, null())" --quiet

# Sediment transport / erosion-deposition
r.mapcalc "tranin = 0.001" --quiet
r.mapcalc "detin = 0.001" --quiet
r.mapcalc "shear_stress = 0.5" --quiet

r.sim.sediment elevation="$LIDAR_DTM_1M" dx="${LIDAR_DTM_1M}_dx" dy="${LIDAR_DTM_1M}_dy" \
	water_depth="depth.30" detachment_coeff="detin" transport_coeff="tranin" \
	shear_stress="shear_stress" man_value=0.04 \
	transport_capacity="transport_capacity" \
	tlimit_erosion_deposition="tlimit_erosion_deposition" \
	sediment_concentration="sediment_concentration" \
	sediment_flux="sediment_flux" \
	erosion_deposition="erosion_deposition" \
	niterations=30 output_step=2 random_seed=3 nprocs=$NPROCS nwalkers=100000

r.mask -r --quiet

# -----------------------------------------------------------------------------
# 5) Solar radiation, TPI, landforms
# -----------------------------------------------------------------------------
echo "Computing solar radiation (r.sun)..."
r.sun elevation="$LIDAR_DTM_1M" slope="${LIDAR_DTM_1M}_slope" aspect="${LIDAR_DTM_1M}_aspect" \
	glob_rad="global_rad_356" insol_time="insol_time_356" day=356 --quiet

r.sun elevation="$LIDAR_DTM_1M" slope="${LIDAR_DTM_1M}_slope" aspect="${LIDAR_DTM_1M}_aspect" \
	glob_rad="global_rad_172" insol_time="insol_time_172" day=172 --quiet

if have_module r.tpi; then
	echo "Computing TPI..."
	r.tpi input="$LIDAR_DTM_1M" output="tpi" --quiet
else
	warn_missing_addon r.tpi
fi

echo "Computing landforms + morphology..."
if have_module r.geomorphon; then
	r.geomorphon elevation="$LIDAR_DTM_1M" forms="${LIDAR_DTM_1M}_landforms" \
		search=21 skip=1 flat=1 dist=0 --quiet
else
	warn_missing_addon r.geomorphon
fi

if have_module r.param.scale; then
	r.param.scale input="$LIDAR_DTM_1M" output="${LIDAR_DTM_1M}_morphology" \
		method=feature size=5 --quiet
else
	warn_missing_addon r.param.scale
fi

echo "Done. Analysis rasters are now in: $PROJECT_PATH/$MAPSET_NAME"
