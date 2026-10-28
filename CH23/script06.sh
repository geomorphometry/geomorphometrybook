#
# start working in PERMANENT (generated previously) and generate new mapset:
# same location/project, so same reference system - but resolution 1 m
#
g.mapset -c stone
#
# We land in the "stone" mapset of the "reunion" location (or project in GRASS GIS 8.4.*)
#
# Import digital elevation data
echo
echo "r.in.gdal input=../reunion_tin_mean21x21.tif output=dem --o --qq"
r.in.gdal input=../reunion_tin_mean21x21.tif output=dem --o --qq

# Set computational region (extent and resolution) to DEM data
echo
echo "g.region rast=dem --qq"
g.region rast=dem --qq

# Colorize DEM data
echo
echo "r.colors -e map=dem color=elevation" --qq
r.colors -e map=dem color=elevation --qq

# Calculate shaded relief map with 5x vertical exaggeration
echo
echo "r.relief input=dem output=shade zscale=5 --o --qq"
r.relief input=dem output=shade zscale=5 --o --qq

# Rockfall vector layer is available from mapset PERMANENT, copy here
echo
echo "g.copy vect=rockfalls@PERMANENT,rockfalls --o --qq"
g.copy vect=rockfalls@PERMANENT,rockfalls --o --qq

# We count the points in each layer
n_rockfalls=`db.select -c sql="select count(*) from rockfalls"`

echo
echo "we have:"
echo "$n_rockfalls rockfalls"
echo


# At this point our mapset "stone" contains three maps:
# -> dem   (raster)
# -> shade (raster)
# -> rockfalls (vector)

# Comma-separated list of column names in vector layer rockfalls
columns=`db.select sql="select * from rockfalls limit 0" separator=comma`

# Select all elements starting from second
columns=`echo $columns | cut -f2- -d","`

# Remove unnecessary columns from vector layer rockfalls: 
echo "removing columns:"
echo $columns

echo
echo "v.db.dropcolumsn map=rockfalls columns=$columns --qq"
#v.db.dropcolumn map=rockfalls columns=$columns --qq

# Calculate slope and curvatures
echo
echo "r.slope.aspect -e elevation=dem slope=slope pcurvature=pcurv tcurvature=tcurv nprocs=4 --o --qq"
r.slope.aspect -e elevation=dem slope=slope pcurvature=pcurv tcurvature=tcurv nprocs=4 --o --qq

# Calculate 5x5 relief
echo
echo "r.neighbors input=dem size=5 method=range nprocs=4 output=relief_5 --o --qq"
r.neighbors input=dem size=5 method=range nprocs=4 output=relief_5 --o --qq

# Add columns to attribute table in rockfalls
echo
echo "v.db.addcolumn map=rockfalls columns=\'slope real, pcurv real, tcurv real, relief_5 real\' --qq"
v.db.addcolumn map=rockfalls columns='slope real, pcurv real, tcurv real, relief_5 real' --qq

# Populate columns with raster values at point locations
echo
echo "v.what.rast map=rockfalls raster=slope column=slope --qq"
v.what.rast map=rockfalls raster=slope column=slope --qq
echo
echo "v.what.rast map=rockfalls raster=pcurv column=pcurv --qq"
v.what.rast map=rockfalls raster=pcurv column=pcurv --qq
echo
echo "v.what.rast map=rockfalls raster=tcurv column=tcurv --qq"
v.what.rast map=rockfalls raster=tcurv column=tcurv --qq
echo
echo "v.what.rast map=rockfalls raster=relief_5 column=relief_5 --qq"
v.what.rast map=rockfalls raster=relief_5 column=relief_5 --qq

# Generate random points to compare distributions of morphometric variables
echo
echo "r.random input=dem npoints=5000 vector=random seed=999 --o --qq"
r.random input=dem npoints=5000 vector=random seed=999 --o --qq


# Add columns to attribute table in random
echo
echo "v.db.addcolumn map=random columns=\'slope real, pcurv real, tcurv real, relief_5 real\' --qq"
v.db.addcolumn map=random columns='slope real, pcurv real, tcurv real, relief_5 real' --qq

# Populate columns with raster values at point locations
echo
echo "v.what.rast map=random raster=slope column=slope --qq"
v.what.rast map=random raster=slope column=slope --qq
echo
echo "v.what.rast map=random raster=pcurv column=pcurv --qq"
v.what.rast map=random raster=pcurv column=pcurv --qq
echo
echo "v.what.rast map=random raster=tcurv column=tcurv --qq"
v.what.rast map=random raster=tcurv column=tcurv --qq
echo
echo "v.what.rast map=random raster=relief_5 column=relief_5 --qq"
v.what.rast map=random raster=relief_5 column=relief_5 --qq

mappe=(random rockfalls)
colonne=(slope pcurv tcurv relief_5)
bins=(45 100 100 50)

ibin=0
for colonna in ${colonne[@]}
do
    nbin=${bins[$ibin]}
    j=0
    for mappa in ${mappe[@]}
    do
	j=$((j+1))
	num=`db.select -c sql="select count(*) from $mappa where ${colonna} is not null"`
	alim=`db.select -c sql="select min(${colonna}) from $mappa where ${colonna} is not null"`
	blim=`db.select -c sql="select max(${colonna}) from $mappa where ${colonna} is not null"`
	db.select -c sql="select ${colonna} from $mappa where ${colonna} is not null" > histo_${colonna}_${j}.txt
	echo
	#	echo "./genera_isto histo_${colonna}_${j}.txt histo_${colonna}_${j}.dat $num 10 $alim $blim ${nbin}"
	#	./genera_isto histo_${colonna}_${j}.txt histo_${colonna}_${j}.dat $num 10 $alim $blim ${nbin}
	rm -f histo_${colonna}_${j}.txt
    done
    ibin=$((ibin+1))
done

# Calculate initiation points locations (sources)
echo
echo "r.mapcalc \"src = if(slope>45 && && relief_5>4 && pcurv>0.02,1,null())\" --o --qq"
r.mapcalc "src = if(slope>45 && relief_5>4 && pcurv>0.02,1,null())" --o --qq

# Geology vector layer from raster layer in PERMANENT
echo
echo "r.to.vect input=geology@PERMANENT output=geology type=area --o --qq"
r.to.vect input=geology@PERMANENT output=geology type=area --o --qq

# We need new columns to store values of terrain parameters
echo
echo "v.db.addcolumn map=geology columns=\'friction real, norm_rest integer, tang_rest integer\' --qq"
v.db.addcolumn map=geology columns='friction real, norm_rest integer, tang_rest integer' --qq

echo
echo "populate column friction"
db.execute sql="update geology set friction=0.30 where value=1"
db.execute sql="update geology set friction=0.30 where value=2"
db.execute sql="update geology set friction=0.40 where value=3"
db.execute sql="update geology set friction=0.80 where value=4"
db.execute sql="update geology set friction=0.30 where value=5"

echo
echo "populate column norm_rest"
db.execute sql="update geology set norm_rest=65 where value=1"
db.execute sql="update geology set norm_rest=65 where value=2"
db.execute sql="update geology set norm_rest=55 where value=3"
db.execute sql="update geology set norm_rest=15 where value=4"
db.execute sql="update geology set norm_rest=65 where value=5"

echo
echo "populate column tang_rest"
db.execute sql="update geology set tang_rest=75 where value=1"
db.execute sql="update geology set tang_rest=25 where value=2"
db.execute sql="update geology set tang_rest=65 where value=3"
db.execute sql="update geology set tang_rest=40 where value=4"
db.execute sql="update geology set tang_rest=75 where value=5"

# Write friction raster
echo
echo "v.to.rast input=geology output=friction use=attr attribute_column=friction --o --qq"
v.to.rast input=geology output=friction use=attr attribute_column=friction --o --qq

# Write normal restitution raster
echo
echo "v.to.rast input=geology output=norm_rest use=attr attribute_column=norm_rest --o --qq"
v.to.rast input=geology output=norm_rest use=attr attribute_column=norm_rest --o --qq

# Write tangential restitution raster
echo
echo "v.to.rast input=geology output=tang_rest use=attr attribute_column=tang_rest --o --qq"
v.to.rast input=geology output=tang_rest use=attr attribute_column=tang_rest --o --qq

echo
echo "r.stone dem=dem sources=src nrest=norm_rest trest=tang_rest friction=friction stop_vel=1.0 counter=stone_output --o --qq"
r.stone dem=dem sources=src nrest=norm_rest trest=tang_rest friction=friction stop_vel=1.0 counter=stone_output --o --qq

