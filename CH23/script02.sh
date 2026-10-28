
##GISDBASE=[your_path]/datagrass
##LOCATION_NAME=reunion
##MAPSET=PERMANENT

# Always set computational region!
echo
echo "g.region rast=dem_10 --qq"
g.region rast=dem_10 --qq

echo
echo "r.mask rast=dem_10 --o --qq"
r.mask rast=dem_10 --o --qq

# flat areas, useful for slope unit delineation, were prepared with an external procedure
echo
echo "r.in.gdal input=flat.tif output=flat --o --qq"
r.in.gdal input=flat.tif output=flat --o --qq

# Either download r.slopeunits software from:
#https://geomorphology.irpi.cnr.it/tools/slope-units
# Or install with [latest version] 
#g.extension r.slopeunits

cvar=0.075
avar=100000

echo
echo "r.slopeunits demmap=dem_10 thresh=5000000 rf=3 maxiteration=50 cvmin=$cvar areamin=$avar slumap=tmp plainsmap=flat --o"
# previous version:
#r.slopeunits demmap=dem_10 thresh=5000000 rf=3 maxiteration=50 cvmin=$cvar areamin=$avar slumap=tmp plainsmap=flat --o
# latest version:
r.slopeunits.create demmap=dem_10 thresh=5000000 rf=3 maxiteration=50 cvmin=$cvar areamin=$avar slumap=tmp plainsmap=flat --o

# We did not use the "cleaning" options in r.slopeunits:
# need to remove small polygons
echo
echo "r.to.vect input=tmp output=tmp type=area --o --qq"
r.to.vect input=tmp output=tmp type=area --o --qq

# rmeove MASK
echo
echo "r.mask -r --qq"
r.mask -r --qq

#let's calculate areas of the units
echo
echo "v.to.db map=tmp option=area columns=area --o --qq"
v.to.db map=tmp option=area columns=area --o --qq

# remove areas smaller then 1000 m^2
echo
echo "v.clean input=tmp output=tmp_clean tool=rmarea threshold=1000 --o --qq"
v.clean input=tmp output=tmp_clean tool=rmarea threshold=1000 --o --qq

# remove attribute table and categories, then add them again - to have a clean vector layer & attribute table
echo
echo "v.db.connect -d map=tmp_clean --qq"
v.db.connect -d map=tmp_clean --qq

echo
echo "db.droptable table=tmp_clean -f --qq"
db.droptable table=tmp_clean -f --qq

echo
echo "v.category input=tmp_clean output=tmp_del option=del cat=-1 --o --qq"
v.category input=tmp_clean output=tmp_del option=del cat=-1 --o --qq

echo
echo "v.category input=tmp_del output=slope_units option=add cat=1 step=1 --o --qq"
v.category input=tmp_del output=slope_units option=add cat=1 step=1 --o --qq

echo
echo "v.db.addtable map=slope_units --qq"
v.db.addtable map=slope_units --qq

echo
echo "v.to.db map=slope_units option=area columns=area --o --qq"
v.to.db map=slope_units option=area columns=area --o --qq

# clean up mapset from unnecessary maps
g.remove type=raster name=tmp -f --qq
g.remove type=vector name=tmp,tmp_clean,tmp_del -f --qq

echo
#
# At this point our mapset "PERMANENT" contains additional two maps:
# -> flat (raster)
# -> slope_units (vector)
#
#
# load workspace file fig01a.gxw to generate Fig. 1(a) of chapter 23 in colors
