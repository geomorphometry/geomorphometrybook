# GRASS

## Chapter 12 Examples

This directory contains Python scripts that demonstrate geomorphometric analyses using [GRASS](https://grass.osgeo.org). The scripts cover various topics such as terrain derivatives, flow accumulation, hydrological modeling, solar radiation, and volumetric analysis.

### Setup

#### Data

```python
# Configuration
PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_NAME = Path(PROJECT_DIR, "ponui")
MAPSET_NAME = "PERMANENT"

DSM_PATH = Path(PROJECT_DIR, "data/dsm.cog.tif")
DSM_NAME = "dsm_10m"

DTM_PATH = Path(PROJECT_DIR, "data/dtm.cog.tif")
DTM_NAME = "dem_10m"
DTM_RELIEF = "dtm_relief"

ISLAND_RESOLUTION = 10  # meters

LIDAR_PATH = Path(PROJECT_DIR, "data/lidar.laz")
LIDAR_DTM_10M = "lidar_dtm_10m"
LIDAR_DTM_1M = "lidar_dtm_1m"
LIDAR_DTM_1M_RELIEF = "lidar_dtm_1m_relief"
LIDAR_DTM_1M_SKYVIEW = "lidar_dtm_1m_skyview"

AOI_REGION = "aoi"
AOI_RESOLUTION = 1  # meters
SAVE_DIR = Path(PROJECT_DIR, "figures")
```

#### Files

- `geomorphometry_in_grass.py`: Main Python script showcasing geomorphometric analyses in GRASS.
- `geomorphometry_in_grass_notebook.ipynb`: Jupyter Notebook version of the main script for interactive exploration.
- `geomorhometry_in_grass.sh`: Shell script to set up the GRASS environment and run the Python scripts.
- `geomorphometry_in_grass.R`: R script for similar geomorphometric analyses using GRASS.
- `gextensions.txt`: List of GRASS add-ons required for the analyses.
