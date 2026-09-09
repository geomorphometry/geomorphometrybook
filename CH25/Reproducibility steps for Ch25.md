# Reproducibility steps for Ch. 25\. Geomorphometry for archaeology

These steps will help you to reproduce the results of the examples shown in Chapter 25 “Geomorphometry for archaeology.” We used GRASS 8.4.2, and these steps are written for that version of GRASS.

# **Section 2\. Basic Archaeological Geomorphometry**

* Deviation from mean elevation: r.mapcalc  
* Slope, aspect, and curvatures: r.slope.aspect  
* Landforms/Geomorphons: r.geomorphon, r.param.scale  
* Hydrology, flow accumulation, basins, and surface wetness: r.watershed  
* Stream network: r.stream.extract  
* Distance to, and elevation above, streams or below ridgelines: r.stream.distance (addon module)  
* Solar irradiation: r.sun

* Examples

  * Use r.random to generate a random sample of points within the watershed boundaries.  
  * Use v.what.rast or v.rast.samp to upload raster values  
  * Use v.univar to calculate univariate statistics for database columns  
  * Use v.db.select to export database to CSV for further analysis and visualization (e.g. Python Pandas and Seaborn)

# **Section 3\. Proximity analysis, movement, and territories**

## Basic distance analysis

* Minimum Euclidean distance between two vector objects: v.distance

* Minimum Euclidean distance between two raster objects: r.distance

* Minimum linear distance between raster features with different distance measures: r.grow.distance

* Distance between two or more coordinates along a raster surface: v.profile

* Example:

  * Use v.distance to upload the shortest straight line distance from a site point to the nearest stream.
  
  * Use v.univar to calculate the mean and standard deviation of the distances, then convert this to the time it would take to walk this distance in hours using the average human walking speed of 5 kilometers per hour (linear distance / 5 kmph \= hours of walking time).
 
  * Compare the distance as calculated by v.profile using the same start and end point.

## Least-cost analysis and movement

* Create friction values: r.mapcalc

* Calculate cost surfaces: r.cost, r.walk

* Delineate least cost route between start and end point(s): r.drain, r.path

* Tabulate linear distances along paths: v.to.db

* Example:

  * Least cost path from sites to streams.

  * Derive stream network for the project area using r.watershed and/or r.streams.
 
  * Use the rasterized version of the extracted stream as the starting points for a least-cost surface calculation using r.walk.
 
  * Use v.what.rast to upload the walking times into the table of nearby archaeological site points.
 
  * Use v.univar to calculate the mean and standard deviation of walking times from the sites to the nearest stream.
 
  * Walking time as calculated by r.walk is in seconds. Convert this to hours by dividing by 3600 (60 seconds per minute x 60 minutes per hour \= 3600 seconds per hour).

## Site catchment modeling and territoriality

* Circular buffers, perhaps concentric: v.buffer, r.buffer

* Simple territory delineation (convex hull, voronoi diagram, delaunay triangles): v.hull, v.voronoi, v.delaunay

* Site catchment and territory modeling using cost surfaces: r.cost, r.walk, r.catchment

* Example:

  * Weighted territory modeling in GRASS GIS. First, create a vector column of “attractiveness” weights for each site based on a metric such as site area. For example, the columns ‘MAX\_W’ and ‘MAX\_L’ contain dimensions of sites in the WHS site database, and this data can be used to calculate the weights. To do so, use v.db.update with the following formula in the “‘query\_column”’ variable:
 
    `(1.0-((‘MAX_W’*’MAX_L’)/(“‘Maximum_area”’)))`

  * Here, “Maximum\_area” is the maximum site area for the largest site in your sample in m2. For the Nabatean towers subset, this value is 12,000m2. The output values scale from 0 for the most attractive sites, to 100 for the least attractive.
 
  * Interpolate these values using v.surf.bspline to to create a seamless “attractiveness landscape” map for the subsample of sites. In v.surf.bspline, select the attractiveness column for the values to interpolate, and use v.distance to calculate the average distance between input site points. For the Nabatean towers sample, this value was 981m. Use this value as the spline step in the North-South and East-West directions, apply a Tychonov regularization parameter of 0.1 (smoother),  and the bicubic interpolation algorithm for best results that avoid under or over-shooting the column values.
 
  * Use the interpolated attractiveness landscape map as the friction map in r.walk to create a cost surface that scales to both attractiveness and empirically calculated walking costs. The areas surrounding the largest sites have the least friction, making them less costly (or more attractive) to travel to. The cost values are no longer quantitative (seconds of walking time), but instead should be viewed as relative values of territoriality, and it is necessary to experiment to determine a cutoff cost value that delineates reasonable territory boundaries.
 
  * For the example in Figure 6, we calculated the 5th percentile of the maximum cost value within 20km radii of all the Nabatean towers using a combination of v.buffer, v.rast.stats and v.db.univar, which was 4,845. Territories can be visualized with the “values” option in d.rast, and/or with the following map algebra equation in the map calculator (replace variable names as necessary):
 
    `“‘territories”’ \= if(“‘territories\_cost\_surface”’ \>= “‘cost cutoff”’, null(), 1\)`

  * The resulting raster map can be converted into a vector polygon map of territories with r.to.vect.

# **Section 4\. Modeling the experiential elements of past landscapes**

## Visibility analysis and visualscapes

* Single and cumulative viewsheds: r.viewshed, r.viewshed.cva

* Example:

  * Use g.extension to install the r.viewshed.cva addon module. Launch it from the Modules tab of the Layer Manager (under “Addons”), or by typing “r.viewshed.cva &” into the terminal (command prompt), and pressing enter.
 
  * Use v.random to create a vector map of 100 random points across the Wadi Hasa region ensuring that the computational region extent aligns to the region of interest.
 
  * Use the random points map as the input viewpoints for r.viewshed.cva. This will produce a cumulative viewshed map of the Wadi Hasa area that estimates the “true” visibility of landscape features in the area. Because 100 sites were used, the visibility scores can be understood as if they were “percent,” otherwise these values would need to be “normalized” by dividing the visibility map by the total number of viewpoints using the map calculator.

## Topographic prominence

* Neighborhood analysis: r.neighbors, r.param.scale, r.geomorphons

* Addon module r.prominence calculates topographic prominence using the method in Llobera (2001).

* Example:

  * Calculate global prominence using the method in Ullah (2015) in GRASS. First, use the module r.geomorphons with the “intensity” geometric measurement at different scales (e.g., 9x9, 13x13, 17x17, and 21x21 cells). Alternatively, use either the module r.neighbors (method \= “average”), or the module r.param.scale (method \= “elev”) to calculate the average elevation across different spatial scales, and then use the map calculator (r.mapcalc) to subtract each resulting map from the original DEM to create a series of topographic prominence maps at these four scales.
 
  * The following map calculator statement provides an example of this (note that elevation needs to remain a floating point value, hence multiplication by 1.0)

    `“prominence_paramscale_9x9” = (1.0 * “elevation”) - “paramscale_elev_9x9”`

  * Finally, for either approach, calculate the average of the set of scalar prominence maps using r.series to estimate the global prominence of different landscape features.

## Inductive statistical modeling approaches

* Boolean map algebra: r.mapcalc, r.mapcalculator

* Linear regression recoding: r.recode

* Vector overlay querying: v.what.rast, v.rast.stats

* Vector column stats: v.univar

* Vector column histogram: v. histogram (addon)

* Data table export: v.out.db

* Python libraries Pandas and Matplotlib or Seaborn for additional data visualization.

* Example:

  * Use the map calculator tool, r.mapcalc, to create a series of conditional statements using different types of boolean expressions and logical operators that create output maps coded “1” for positive and “0” for negative results.
  
  * To keep values below a threshold, use the boolean less-than-or-equal to, “\<=”:

    `if(“input_map” <= “threshold”, 1, 0)`

  * To keep values above a threshold, use the boolean greater-than-or-equal-to, “\>=”:

    `if(“input_map” >= “threshold”, 1, 0)`

  * To keep values between an upper and a lower boundary, you will need to use the “and” logical operator, “&&”, between the two previous boolean statements:

    `if(“input_map” >= “lower threshold” && “input_map” <= “upper threshold”, 1, 0)`

  * To keep values above and below of an upper and a lower boundary (but not between), you will need to use the “or” logical operator, “||”, instead:

    `if(“input_map” <= “lower threshold” || “input_map” >= “upper threshold”, 1, 0)`

  * Substitute the real map names for “input\_map” and the real threshold values you chose for “threshold”, and use sensible output map names. These new maps are binary maps (they contain values of only 1 or 0). Assemble the binary maps into a simple predictive model through a simple averaging formula in the map calculator (r.mapcalc):
 
    `(“binary_map1” + “binary_map2” + “binary_map3” + “binary_map4”) / 4.0`

  * Again, substitute the real map names and ensure that the denominator is the actual number of input maps you used (e.g., if you used five input maps, the number should be 5.0). Be sure to include the decimal point in the denominator to produce a floating point map with decimal values ranging between 0.0 and 1.0 (GRASS will calculate an integer map if no decimal is detected in the denominator, and the output map will also be binary). Areas that have values close to 1.0 are very likely to have sites, and areas that have values close to 0.0 are very unlikely to contain sites.
 
  * Alternatively, weight one or more of the input variables so that they will carry more influence in the output model. To weight an input variable, multiply it by a weighting factor, and then account for the weighting factor in the denominator of the averaging formula:

    `( (“binary_map1” * 2) \+ “binary_map2” + “binary_map3” + “binary_map4”) / 5.0`

  * Note the use of an additional set of parentheses in this formula because the order of operations is important when doing raster math. This ensures that the weighting multiplication takes place before the addition. 

## Deductive modeling approaches, Model verification, validation, testing, and application

* Site sub-sampling and partitioning: v.db.select, v.kcv

* Spatial querying at points, around points, within polygons: v.what.rast, v.sample v.rast.stats

* Column statistics and plots for vector tables: v.univar, d.vect.colhist

* Example:

  * Use a series of SQL queries in v.db.select to extract a small subset of similar sites from one of the larger sets of survey points (this will make a new vector points map). Sample sets should be related functionally and temporally to control for variation in site location decision behavior across time or between categories of sites. Ideally the sample should contain \~ n \>= 50 sites.
    
  * Divide this site sample into training and testing/validation subsamples. A rule of thumb is to reserve \~20% of the sample population as a testing/validation subset, and to build the model with the remaining 80% of sites, so use v.kcv to randomly partition point set into five partitions (this only creates partition labels in a new column of the vector table).
 
  * Use v.db.select to create a training set with the first four partitions and separate testing set with the fifth partition.
 
  * Proceed with predictive modeling using the training dataset (use any method described above).
 
  * Use v.what.rast to upload the values from the predictive model output map into the table of the testing/validation sites.
 
  * Use v.univar to calculate descriptive statistics for this new column and/or create a histogram of the values using d.vect.colhist to interpret the goodness of fit of your model to the training/validation set.
 
  * The GRASS addon extension r.learn.ml2 uses the Python Scikit library to enable multiple advanced machine learning algorithms to be applied and validated.

