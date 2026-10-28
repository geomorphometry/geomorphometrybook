
##GISDBASE=[your_path]/datagrass
##LOCATION_NAME=reunion
##MAPSET=PERMANENT

# Always set the computational region!
echo
echo "g.region rast=dem_10 --qq"
g.region rast=dem_10 --qq

# We need zonal statistics within slope unit polygons. 
# First we calculate the base variables:
# -> slope,
# -> profile curvature,
# -> northerness,
# -> easterness,
# -> TWI, (topographic wetness index)
# -> geology,
# -> relief (for grid approach)

# 1 - slope and profile curvature maps
echo
echo "r.slope.aspect -e elevation=dem_10 slope=slope pcurvature=pcurv --o --qq"
r.slope.aspect -e elevation=dem_10 slope=slope pcurvature=pcurv --o --qq

# 1.5 - relief, 3x3, 5x5 7x7, 9x9 windows - this is only useful for grid-based analysis
echo
echo "r.neighbors input=dem_10 method=range size=3 output=relief_3x3 --o --qq"
r.neighbors input=dem_10 method=range size=3 output=relief_3x3 --o --qq
r.mask rast=slope --o --qq
r.grow input=relief_3x3 output=tmp radius=3.01 --o --qq
r.mask -r --qq
g.rename rast=tmp,relief_3x3 --o --qq

echo
echo "r.neighbors input=dem_10 method=range size=5 output=relief_5x5 --o --qq"
r.neighbors input=dem_10 method=range size=5 output=relief_5x5 --o --qq
r.mask rast=slope --o --qq
r.grow input=relief_5x5 output=tmp radius=3.01 --o --qq
r.mask -r --qq
g.rename rast=tmp,relief_5x5 --o --qq

echo
echo "r.neighbors input=dem_10 method=range size=3 output=relief_7x7 --o --qq"
r.neighbors input=dem_10 method=range size=5 output=relief_7x7 --o --qq
r.mask rast=slope --o --qq
r.grow input=relief_7x7 output=tmp radius=5.01 --o --qq
r.mask -r --qq
g.rename rast=tmp,relief_7x7 --o --qq

echo
echo "r.neighbors input=dem_10 method=range size=5 output=relief_9x9 --o --qq"
r.neighbors input=dem_10 method=range size=7 output=relief_9x9 --o --qq
r.mask rast=slope --o --qq
r.grow input=relief_9x9 output=tmp radius=7.01 --o --qq
r.mask -r --qq
g.rename rast=tmp,relief_9x9 --o --qq

# 2 - topographic wetness index
echo
echo "r.topidx input=dem_10 output=twi --o --qq"
r.topidx input=dem_10 output=twi --o --qq

# 3 - northerness and easterness
echo
echo "r.northerness.easterness elevation=dem_10 --o --qq (modified to include boundary values:"
echo "                                                     added flags=\"e\" to the script !)"   
r.northerness.easterness elevation=dem_10 --o --qq
g.rename rast=dem_10_northerness,nthns --o --qq
g.rename rast=dem_10_easterness,easns --o --qq
g.remove type=raster name=dem_10_northerness_slope -f --q

# geology was prepared beforehand (source in chapter 22)
echo
echo "r.in.gdal input=geology.tif output=geology --o --qq"
r.in.gdal input=geology.tif output=geology --o --qq

# we want an integer maps
echo
echo "r.mapcalc \"tmp = int(geology)\" --o --qq"
r.mapcalc "tmp = int(geology)" --o --qq
g.rename rast=tmp,geology --o --qq


# the smallest covegage is 7% for geology class=3, so all classes are relevant
echo
echo "r.univar map=geology zones=geology -t separator=space --qq | cut -f1,3 -d\' \' | tail -n 13"
r.univar map=geology zones=geology -t separator=space --qq | cut -f1,3 -d' ' | tail -n 13

#
# Now we calculate zonal statistics
#
# morphometric variables
#

echo
echo "v.rast.stats -c map=slope_units raster=slope method=average,stddev column_prefix=slope --o --qq"
v.rast.stats -c map=slope_units raster=slope method=average,stddev column_prefix=slope --o --qq

echo
echo "v.rast.stats -c map=slope_units raster=pcurv method=average,stddev column_prefix=pcurv --o --qq"
v.rast.stats -c map=slope_units raster=pcurv method=average,stddev column_prefix=pcurv --o --qq

echo
echo "v.rast.stats -c map=slope_units raster=twi method=average,stddev column_prefix=twi --o --qq"
v.rast.stats -c map=slope_units raster=twi method=average,stddev column_prefix=twi --o --qq

echo
echo "v.rast.stats -c map=slope_units raster=nthns method=average,stddev column_prefix=nthns --o --qq"
v.rast.stats -c map=slope_units raster=nthns method=average,stddev column_prefix=nthns --o --qq

echo
echo "v.rast.stats -c map=slope_units raster=easns method=average,stddev column_prefix=easns --o --qq"
v.rast.stats -c map=slope_units raster=easns method=average,stddev column_prefix=easns --o --qq

#
# categorical variables (geology)
#

#store number of cells in each slope unit
echo
echo "v.rast.stats -c map=slope_units raster=dem_10 method=number column_prefix=cell --o --qq" 
v.rast.stats -c map=slope_units raster=dem_10 method=number column_prefix=cell --o --qq

cats_geo=`r.describe map=geology -1n --qq`

echo
j=0
for geo in ${cats_geo[@]}
do
    j=$((j+1))
    r.mapcalc "tmp = if(geology==${j},1,null())" --o --qq
    echo "v.rast.stats -c map=slope_units raster=tmp method=number column_prefix=geo${j} --o --qq"
    v.rast.stats -c map=slope_units raster=tmp method=number column_prefix=geo${j} --o --qq
    g.remove type=rast name=tmp -f --qq
    v.db.addcolumn map=slope_units columns="perc_geo_${j} real" --qq
    db.execute sql="update slope_units set perc_geo_${j}=(geo${j}_number*1.0)/(cell_number*1.0)" --qq
    v.db.dropcolumn map=slope_units columns=geo${j}_number --qq
done
echo

# remove unecessary columns
echo
echo "v.db.dropcolumn map=slope_units columns=cell_number,area --qq"
v.db.dropcolumn map=slope_units columns=cell_number,area --qq

# At this point our mapset "PERMANENT" contains additional maps:
# -> slope (raster)
# -> pcurv (raster)
# -> easns (raster)
# -> nthns (raster)
# -> relief_3x3 (raster)
# -> relief_5x5 (raster)
# -> relief_7x7 (raster)
# -> relief_9x9 (raster)
# -> twi (raster)
# -> geology (raster)
