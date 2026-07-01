# geomorphometrybook
## The HAND algorithm
All PCRaster tools have the same name as their equivalent PCRaster Python functions that 
can be used in the QGIS Python Console. Using the functions directly in scripts reduces the 
overhead introduced by the model designer, which otherwise needs to load tools and write 
intermediate results. Intermediate results can be kept in memory, and only final results can be 
written to disk. The *1_HAND.py* script is an example to calculate the Height Above Nearest Drainage 
(HAND) using the PCRaster Python package in the QGIS Python Console. 

## Prerequisites
To run the code you need to install:
* [QGIS Desktop](https://qgis.org/download/)
* [PCRaster](https://jvdkwast.github.io/qgis-processing-pcraster/)
* PCRaster Tools plugin

Inputs to the model (a boolean drainage raster, DEM and flow direction raster) need to be provided in PCRaster format.
