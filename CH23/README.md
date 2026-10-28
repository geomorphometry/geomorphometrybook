# CHAPTER 23 – Modelling Mass Movements and Landslide Susceptibility

by Massimiliano Alvioli, Martin Mergili, and Alexander Brenning

Please report issus to: massimiliano.alvioli[AT]cnr.it, alexander.brenning[AT]uni-jena.de

## Intro

The topics discussed in Chapter 23 were illustrated with results obtained
mostly within GRASS GIS and R. The contents of the chapter are summarized
as follows:

* spatial modelling of potential slope instability by geomorphometry
* statistical and machine learning methods for landslide susceptibility
* delineation of slope units for susceptibility zonation
* 3D kinematical rockfall runout model
* multiphase dynamical mass flow model

We include example code to produce all the figures in the chapter corresponding
to the first four points. The code consists in simple bash script, which can be
run within a GRASS GIS terminal. Section "23.7 Important sources" in the book
contain web links to obtain relevant software, and additional resources to have
additional insinght in their use.

The material is organized is six bash scripts. Use of the scripts was tested in
ubuntu Linux (in a Windows Subsystem for Linux shell), and it requires the following
input maps, provided in the examples:

* dem_10.tif - elevation data reasampled at 10 m
* flat.tif - pre-calculated raster map of flat areas
* geology.tif - rasterized geology of the area
* reunion_tin_21x21.tif - elevation data at 1 m, bundled with the main example materials of the book

Their content is as follows:

### script01.sh

generates a GRASS GIS location using the reference system information contained
in the georeferenced dem_10.tif file (elevation data for La Union study area,
resampled at 10 m).

After the code is run, the mapset PERMANENT contains the new maps:

* dem_10 (raster)
* shade_10 (raster)
* landslides (vector)
* slides (vector)
* rockfalls (vector)
* flows (vector)

### script02.sh

Prepares the slope units vector layer.

After run, PERMANENT contains the new maps:

* flat (raster)
* slope_units (raster)

Load bundled file fig01a.gxw to generate Fig. 1(a) of chapter 23 in colors

### script03.sh

Calculates the input layers corresponding to the input variables for multivariate
statistical modeling of landslide susceptibility. Base variables are: slope, profile
curvature, northerness, easterness, topographic wetness index, geology, pedology,
relief.

After run, PERMANENT contains the new maps:

*  slope (raster)
*  pcurv (raster)
*  easns (raster)
*  nthns (raster)
*  relief_3x3 (raster)
*  relief_5x5 (raster)
*  relief_7x7 (raster)
*  relief_9x9 (raster)
*  twi (raster)
*  geology (raster)

### script04.sh

Calculates the slope units-based landslide susceptibility map with the GAM models.
Used the external R code susc_slopeunits_gam.R (included). Creates the working
directory susc_slopeunits_gam. 

After run, PERMANENT contains the new maps:

* susc_slopeunits_fit_gam (raster)
* susc_slopeunits_fit_glm (raster)

Load workspace file fig03[a-d].gxw to generate Figs. 3(a-d) of chapter 23 in bw.

### script05.sh

Calculates the grid-based landslide susceptibility map with the GAM and GLM models.
Used the external R code susc_grid_gam.R (included). Creates the working directory susc_grid_gam. 

After run, PERMANENT contains the new maps:

* susc_grid_predict_gam (raster)
* susc_grid_predict_glm (raster)

### script06.sh

Prepares input data & run the 3D rockfall model r.stone, in a new mapset called "stone".

After run, the mapset stone contains the new maps:

* dem   (raster)
* shade (raster)
* geology
* rockfalls (vector)
* src (raster)
* norm_rest (raster)
* tang_rest (raster)
* friction (raster)
* stone_output (raster)
