# geomorphometrybook

## Chapter 26: Geomorphometry in Spatial Hydrological Modeling

This chapter focuses on geomorphometry in spatial hydrological modeling and 
its downstream applications, such as watershed management scenario optimization, 
using high or medium spatial-resolution gridded DEM. 

The code used in the case study of this chapter includes 
[AutoFuzSlpPos](https://github.com/lreis2415/AutoFuzSlpPos) and 
[SEIMS](https://github.com/lreis2415/SEIMS).

### AutoFuzSlpPos
AutoFuzSlpPos (short for “Automated Fuzzy Slope Position”), is an automatic tool 
to derive fuzzy slope positions based on the prototype-based inference method proposed by 
[Qin et al. (2009)](https://www.sciencedirect.com/science/article/pii/S0169555X0900155X).

By default, this tool requires only one input dataset (i.e., a gridded DEM of the study area) . 
AutoFuzSlpPos consists of three major parts: 
(1) preparing topographic attributes, 
(2) extracting typical locations, and 
(3) calculating similarity for each type of slope position. 

The default setting uses the system of five basic slope positions, 
i.e., ridge, shoulder slope, backslope, footslope, and valley.
AutoFuzSlpPos can also be configured to derive three types of slope positions,
i.e., ridge, backslope, and valley, which were adopted in the case study of this chapter.

The core computing part of AutoFuzSlpPos is developed based on 
the [TauDEM](https://github.com/dtarb/TauDEM) parallelized framework written in C++.
The automated workflow part of AutoFuzSlpPos is written in Python.

The installation of AutoFuzSlpPos includes compiling the C++ part using any compilers that support C++11 and 
creating a new Python environment using `conda`. 
After installation, readers can run the demo script `AutoFuzSlpPos/demo/demo_sdemo_fuzslppos.py` to 
execute AutoFuzSlpPos with the demo data located in `AutoFuzSlpPos/data`. 

For more details, please refer to the [online user manual](https://lreis2415.github.io/AutoFuzSlpPos/) and 
the [paper published in Geomorphology](https://www.sciencedirect.com/science/article/pii/S0169555X17300612).

### SEIMS
SEIMS (short for Spatially Explicit Integrated Modeling System), is 
a modular and parallelized watershed modeling framework 
that focuses on building and performing watershed process models in a plug-and-play way, 
and on conducting scenario optimization of watershed best management practices (BMPs).

SEIMS is implemented using standard C++ and Python to be cross-platform compatible. 
SEIMS uses CMake to manage the entire project for compatibility with mainstream compilation environments. 
The compiled C++ programs include the SEIMS main programs (the OpenMP version and the MPI&OpenMP version), 
the SEIMS module library (which includes Hydrology, Erosion, Nutrient, Plant Growth, BMP Management, etc), and 
executable programs for data preprocessing. 
Python is used for utility tools including 
data preprocessing, calibration, sensitivity analysis, scenario analysis, and so on.

The geomorphometry used in SEIMS includes two parts:
+ data preprocessing (`SEIMS/seims/preprocess`) based on 
[extended TauDEM (including AutoFuzSlpPos)](https://github.com/lreis2415/TauDEM_ext)
+ scenario analysis (`SEIMS/seims/scenario_analysis`) based on different types of spatial units, 
including HRU, field, hydrological connected field, and slope position units.

Readers can manually install SEIMS by following the 
[installation instruction](https://lreis2415.github.io/SEIMS/getstart_download_installation.html), 
or using the prebuilt [Docker image](https://github.com/lreis2415/SEIMS/pkgs/container/seims). 

SEIMS provides a series of test scripts in `SEIMS/seims/test` to help users get started quickly.

For more details, please refer to the [online user manual](10.1016/j.envsoft.2019.104526) and 
the [paper published in ](http://www.sciencedirect.com/science/article/pii/S1364815218309241).
