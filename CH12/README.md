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

* `geomorphometry_in_grass.py`: Canonical Python script. Reproduces every figure shown in the chapter (plus additional 3D views) using helper abstractions for color schemes, map composition, and figure export.
* `geomorphometry_in_grass.ipynb`: Verbose Jupyter Notebook version of the workflow. Mirrors the Python script section-by-section but inlines the abstractions (color rules, `gj.Map` composition, 3D figure code) so each GRASS command and rendering step is visible. Recommended as the learning aid.
* `geomorphometry_in_grass.sh`: Bash CLI version of the analysis workflow (no figure generation). Useful for headless / batch runs.
* `geomorphometry_in_grass.R`: R version of the analysis workflow via the [`rgrass`](https://cran.r-project.org/package=rgrass) package. Like the bash script, it computes the analysis rasters without generating figures.
* `gextensions.txt`: List of GRASS add-ons required for the analyses.

### Running the Scripts

#### Python

1. Ensure you have Python 3.10+ installed.
2. Install the required Python packages using pip:

    * matplotlib
    * Pillow
    * numpy

    Or install them using the `requirements.txt` file:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
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
    jupyter notebook geomorphometry_in_grass.ipynb
    ```

#### R

The R version uses the [`rgrass`](https://cran.r-project.org/package=rgrass) package to drive GRASS from R. Like the bash script, it performs the analysis without generating figures.

1. Ensure you have GRASS 8.5+ installed and available as `grass` on your `PATH`.

2. Install the `rgrass` package from CRAN:

    ```r
    install.packages("rgrass")
    ```

3. Install the required GRASS add-ons listed in `gextensions.txt` (same set used by the bash script).

4. Run the script:

    ```bash
    Rscript geomorphometry_in_grass.R
    ```

#### Shell

The `geomorphometry_in_grass.sh` script is a simplified version of the Python script that focuses on the core GRASS commands without generating figures or maps. To run the shell script, follow these steps:

1. Ensure you have GRASS installed and available as `grass` in your command line.

2. Install the required GRASS add-ons listed in `gextensions.txt` using the `g.extension` command in GRASS. You can do this by running the following commands in the GRASS command line or the script will install them for you:

    ```bash
    g.extension extension=r.flowaccumulation
    g.extension extension=r.stream.order
    g.extension extension=r.stream.distance
    g.extension extension=r.hand
    g.extension extension=r.tpi
    g.extension extension=r.skyview
    ```

3. Make the shell script executable:

    ```bash
    chmod +x geomorphometry_in_grass.sh
    ```

4. Run the shell script:

    ```bash
    ./geomorphometry_in_grass.sh
    ```

### Running on Windows

All four versions drive GRASS, which runs on Windows, so the analysis works
there. The scripts are written for a Unix shell with `grass` on the `PATH`, so
pick one of the two paths below and then follow the per-language steps above.

#### Recommended: WSL2

The simplest, most reliable option is the Windows Subsystem for Linux, which
runs the scripts exactly as on Linux with no edits.

1. Install WSL2 with Ubuntu (in PowerShell, once):

    ```powershell
    wsl --install
    ```

2. Open the Ubuntu shell, install GRASS 8.5+, Python, and (for the R version) R,
   then clone this repository inside WSL.
3. Follow the **Python**, **R**, or **Shell** steps above unchanged.

#### Native Windows (OSGeo4W)

1. Install GRASS with the [OSGeo4W installer](https://grass.osgeo.org/download/windows/).
   It bundles PDAL, which `r.in.pdal` and `v.in.pdal` require.
2. Launch the **OSGeo4W Shell** (from the Start menu), not `cmd` or PowerShell,
   so that `grass` and the GRASS tools are on the `PATH`.
3. From that shell, run the Python script or notebook, or the R script:

    ```bat
    python geomorphometry_in_grass.py
    jupyter notebook geomorphometry_in_grass.ipynb
    Rscript geomorphometry_in_grass.R
    ```

Notes for native Windows:

* The `geomorphometry_in_grass.sh` version needs a Bash shell (WSL2 or Git Bash);
  it does not run in `cmd` or PowerShell.
* If the Python script reports `GRASS executable 'grass' not found on PATH`, you
  are not in the OSGeo4W Shell. Open it and retry, or set the `GISBASE`
  environment variable to your GRASS installation.
* Add-ons install automatically when you run the Python script, or install them
  manually with the `g.extension` commands listed under **Shell** above.
* Download the data from the Zenodo links above and unzip the LiDAR archive so
  that `data/LAS_ponui_island_lidar.laz` exists.
