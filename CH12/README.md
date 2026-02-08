# Chapter 12 - GRASS Examples

This directory contains Python scripts that demonstrate geomorphometric analyses using [GRASS](https://grass.osgeo.org). The scripts cover various topics such as terrain derivatives, flow accumulation, hydrological modeling, solar radiation, and volumetric analysis.

## Setup

### Install GRASS

To run the scripts, you will need to have GRASS (version >=8.5) installed on your system. You can download it from the [GRASS website](https://grass.osgeo.org/download/).

#### Data

The data of Ponui Island can be downloaded from [Zenodo](https://doi.org/10.5281/zenodo.18314107). The dataset includes a Digital Surface Model (DSM), Digital Terrain Model (DTM), and LiDAR point cloud data. Below are the direct download links for the DSM, DTM, and LiDAR data:

* [Download DSM Ponui Island (Zenodo)](https://zenodo.org/records/18314107/files/DEM_ponui_island_dsm.tif?download=1)
* [Download DTM Ponui Island (Zenodo)](https://zenodo.org/records/18314107/files/DEM_ponui_island_dtm.tif?download=1)
* [Download LAS Ponui Island LiDAR (Zenodo)](https://zenodo.org/records/18314107/files/LAS_ponui_island_lidar.zip?download=1)

By default, the scripts are set up to download the DSM and DTM directly from Zenodo. If you prefer to use local files, simply uncomment the lines in the configuration section of the script and adjust the paths accordingly. However, the LiDAR data must be downloaded and extracted manually, as the `v.in.pdal` command does not currently support use of the GDAL virtual file system (`vsicul` and `vsizip`).

#### Files

* `geomorphometry_in_grass.py`: Main Python script showcasing geomorphometric analyses in GRASS.
* `geomorphometry_in_grass_notebook.ipynb`: Jupyter Notebook version of the main script for interactive exploration.
* `geomorhometry_in_grass.sh`: Shell script to set up the GRASS environment and run the Python scripts.
* `geomorphometry_in_grass.R`: R script for similar geomorphometric analyses using GRASS.
* `gextensions.txt`: List of GRASS add-ons required for the analyses.

### Running the Scripts

#### Python

1. Ensure you have Python 3.8 or higher installed.
2. Install the required Python packages using pip:

    * matplotlib
    * Pillow
    * numpy

    Or install them using the `requirements.txt` file:

    ```bash
    pip install -r requirements.txt
    ```

    or if using uv:

    ```bash
    uv pip install -r requirements.txt
    ```

3. Run the Python script:

    ```bash
    python geomorphometry_in_grass.py
    ```

    Alternatively, you can run the Jupyter Notebook for an interactive experience:

    ```bash
    jupyter notebook geomorphometry_in_grass_notebook.ipynb
    ```
