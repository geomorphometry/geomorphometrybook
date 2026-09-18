# Geomorphometry

## Chapter 21 -- Soil Mapping Applications 


This chapter focuses on soil mapping applications. The chapter's case study section demonstrates how two sampling designs are implemented and how those samples are used to create a map of soil organic carbon. 
Here you find the code to 

1. derive the land surface parameters used for this sampling design and the predictive mapping 

2. propose locations for soil sampling for model calibration and validation 

3. create a digital soil map with random forest machine learning approach.  

### Software requirements 

You need an installation of [R Software for Statistical Computing](https://cran.r-project.org/) and install the following R packages: 
``` 
install.packages('sf', 'terra', 'Rsagacmd', 'fields', 'ranger', 'ggplot2')
```

Further, you need an installation of [SAGA GIS](https://saga-gis.sourceforge.io/)
