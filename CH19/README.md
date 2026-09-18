# Geomorphometry Using Open-Source Programming Languages

This repository contains code and setup instructions to run the examples from the chapter "Geomorphometry Using Open-Source Programming Languages" from the second edition of the book *Geomorphometry: Software, Concepts, Applications*.

## Requirements

### Files

Each language has its own dedicated folder containing the main script, scripts for installing dependencies, and a README with language-specific instructions.

The code assumes that the required data are contained within the shared `Data` folder in `CH19`. The required data can either be downloaded manually from Zenodo or downloaded automatically using the provided scripts.

#### Option 1: Automatic download and preparation

To automatically download the required files, open a terminal (MacOS/Linux) or Command Prompt (Windows) and navigate to the `CH19` folder using the `cd` command. For example:

**Linux/macOS:**

    cd "/path/to/CH19"

**Windows:**

    cd /d "C:\path\to\CH19"

Then download the required data by running:

**Linux/macOS:**

    bash download_data.sh

**Windows:**

    download_data.cmd

After the downloads are complete, extract and rename the files by running:

**Linux/macOS:**

    bash rename_data.sh

**Windows:**

    rename_data.cmd

The scripts will place the downloaded files in the `Data` folder, extract the required ZIP archives, and rename the data files to match the filenames used by the chapter code.

#### Option 2: Manual download and preparation

The data are available from the following Zenodo repositories:

- **Primary dataset:** https://doi.org/10.5281/zenodo.18314107
- **LAS dataset:** https://doi.org/10.5281/zenodo.22769771

Download the following files and place them in the `Data` folder:

- `LAS_ponui_island_lidar.zip`
- `LAS_ponui_island_lidar_las.zip`
- `VECT_ponui_buffer_10m.zip`
- `DEM_ponui_island_dsm.tif`
- `DEM_ponui_island_dtm.tif`

The filenames in the Zenodo repositories differ from those used in the chapter and accompanying code. Extract the three ZIP archives and rename the resulting data files according to the following crosswalk:

| Filename used in chapter | Zenodo filename | ZIP archive |
| --- | --- | --- |
| `ponui.las` | `LAS_ponui_island_lidar.las` | `LAS_ponui_island_lidar_las.zip` |
| `ponui.laz` | `LAS_ponui_island_lidar.laz` | `LAS_ponui_island_lidar.zip` |
| `ponui_buffer10m.gpkg` | `ponui_buffer_10m.gpkg` | `VECT_ponui_buffer_10m.zip` |
| `ponui_island_dsm.tif` | `DEM_ponui_island_dsm.tif` | — |
| `ponui_island_dtm.tif` | `DEM_ponui_island_dtm.tif` | — |

After extraction and renaming, the `Data` folder should contain the following five files required by the chapter code:

- `ponui.las`
- `ponui.laz`
- `ponui_buffer10m.gpkg`
- `ponui_island_dsm.tif`
- `ponui_island_dtm.tif`

### Programming Languages

- R and RStudio can be downloaded and installed from https://posit.co/download/rstudio-desktop/
- The Anaconda/Miniconda Python distribution can be downloaded and installed from https://www.anaconda.com/download
- Julia can be downloaded and installed from https://julialang.org/install/

### Integrated Development Environment

While R, Python, and Julia code can be all be run directly from a terminal, using 
an Integrated Development Environment (IDE) makes running, debugging, and organizing code easier.
Some popular options for each language are provided below:

**R**
- [Rstudio](https://posit.co/download/rstudio-desktop/)
- [Positron](https://positron.posit.co/)
- [VS Code + R Extension](https://code.visualstudio.com/docs/languages/r)

**Python**
- [PyCharm](https://www.jetbrains.com/pycharm/)
- [VS Code + Python Extension](https://code.visualstudio.com/docs/languages/python)
- [Spyder](https://www.spyder-ide.org/)
- [Positron](https://positron.posit.co/)

**Julia**
- [VS Code + Julia Extension](https://code.visualstudio.com/docs/languages/julia)

### Packages

Additional packages, that are not part of the base set of functions for the language,
are required for each section. Instructions for each language are provided in the 
README specific for each language.

## Citation

If you use this code in your work, please cite the book chapter as follows:

Ilich, A.R., Nowosad, J., Hugonnet, R., & Pronk, M. (2026). Chapter 19 - Geomorphometry using open-source programming languages. In H.I. Reuter, C.H. Grohmann, & V. Lecours (Eds.), *Geomorphometry: Concepts, Software, Applications* (2nd ed., pp. 553–581). Elsevier. https://doi.org/10.1016/B978-0-44-333376-7.00030-6