
# Generate GRASS GIS location using the reference system information in the dem_10.tif file:
#
#mkdir datagrass
#grass -c dem_10.tif datagrass/reunion
#
# We land in the "PERMANENT" mapset of the "reunion" location (or project in GRASS GIS 8.4.*)
#
# Import digital elevation data
echo
echo "r.in.gdal input=dem_10.tif output=dem_10 --o --qq"
r.in.gdal input=dem_10.tif output=dem_10 --o --qq

# Set computational region (extent and resolution) to DEM data
echo
echo "g.region rast=dem_10 --qq"
g.region rast=dem_10 --qq

# Colorize DEM data
echo
echo "r.colors -e map=dem_10 color=elevation" --qq
r.colors -e map=dem_10 color=elevation --qq

# Calculate shaded relief map of resampled DEM data
echo
echo "r.relief input=dem_10 output=shade_10 zscale=5 --o --qq"
r.relief input=dem_10 output=shade_10 zscale=5 --o --qq

# Import shapefile containing various types of landslides, limited to dem_10 region
echo
echo "v.import extent=region input=Movements output=movements --o --qq"
v.import extent=region input=Movements output=movements --o --qq

# Check different types of landslides in the inventory
echo
echo "db.select sql=\"select distinct(libelleTyp) from movements\" --qq"
db.select sql="select distinct(libelleTyp) from movements" --qq

# We are interested in slides ("Glissement")
echo
echo "v.extract input=movements output=slides where=\"libelleTyp=\'Glissement\'\" --o --qq"
v.extract input=movements output=slides where="libelleTyp='Glissement'" --o --qq

# Let's collect rockfalls ("Chute de blocs / Eboulement") and flows ("Coulée") as well
echo
echo "v.extract input=movements output=rockfalls where=\"libelleTyp like \'Chute%\'\" --o --qq"
v.extract input=movements output=rockfalls where="libelleTyp like 'Chute%'" --o --qq
echo
echo "v.extract input=movements output=flows where=\"libelleTyp=\'Coulée\'\" --o --qq"
v.extract input=movements output=flows where="libelleTyp='Coulée'" --o --qq

# We patch the three types together in one vector layer "landslides"
echo
echo "v.patch -e input=slides,rockfalls,flows output=landslides --o --qq"
v.patch -e input=slides,rockfalls,flows output=landslides --o --qq

# We count the points in each layer
n_landslides=`db.select -c sql="select count(*) from landslides"`
n_slides=`db.select -c sql="select count(*) from slides"`
n_rockfalls=`db.select -c sql="select count(*) from rockfalls"`
n_flows=`db.select -c sql="select count(*) from flows"`

echo
echo "we have:"
echo "$n_landslides total landslides, of which:"
echo "$n_slides slides,"
echo "$n_rockfalls rockfalls,"
echo "$n_flows flows."
echo

# Remove unnecessary data
echo
echo "g.remove type=vector name=landslides -f --qq"
g.remove type=vector name=landslides -f --qq

echo

#
# At this point our mapset "PERMANENT" contains these maps:
# -> dem_10 (raster)
# -> shade_10 (raster)
# -> landslides (vector)
# -> slides (vector)
# -> rockfalls (vector)
# -> flows (vector)

