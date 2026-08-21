# Geomorphometry Using Open-Source Programming Languages

This repository contains code and setup instructions to run the examples from the chapter "Geomorphometry Using Open-Source Programming Languages" from the second edition of the book *Geomorphometry: Software, Concepts, Applications*.

## Requirements

### Files
Each language has its own dedicated folder with the main script as well as scripts for installing dependencies and a ReadME with language specific instructions.
The code here assumes that required data is contained within a folder called "Data". The neccessary data files are "ponui.las", "ponui.laz", 
"ponui_buffer10m.gpkg", "ponui_island_dsm.tif", and "ponui_island_dtm.tif".
These data can be downloaded from ??????????????.

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
- [Julia for Positron](https://open-vsx.org/extension/ntluong95/positron-julia)

### Packages

Additional packages, that are not part of the base set of functions for the language,
are required for each section. Instructions for each language are provided in the 
README specific for each language.

<!--
## Citation

If you use this code in your work, please cite the book chapter as follows:

> 

-->
