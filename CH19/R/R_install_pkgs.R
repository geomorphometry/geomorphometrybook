# Run script to install needed R packages

needed_packages <- c("sf", "terra", "lidR", "MultiscaleDTM", "SurfRough",
    "dplyr", "ggplot2", "tmap", "cetcolor","viridis", "reshape2", "here") # Needed packages

install.packages(needed_packages[!(needed_packages %in% installed.packages())]) # Install only the packages you don't have

# install.packages(needed_packages) # alternatively can install/update all needed packages