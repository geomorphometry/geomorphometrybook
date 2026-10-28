
##GISDBASE=[your_path]/datagrass
##LOCATION_NAME=reunion
##MAPSET=PERMANENT

# Always set the computational region!
echo
echo "g.region rast=dem_10 --qq"
g.region rast=dem_10 --qq

# Remove mask, if any
echo
echo "r.mask -r --qq"
r.mask -r --qq

# Create new empty input, output folders in existing folder susc_grid_gam
rm -rf susc_grid_gam/input
rm -rf susc_grid_gam/output
mkdir susc_grid_gam/input
mkdir susc_grid_gam/output
# Store file name for values of metrics in a variable & write headers
aucfile=susc_grid_gam/output/output_metrics.txt
rm -f ${aucfile}
echo "Combination, AUC_ROC, Brier Score:" > $aucfile

# Extract landslide points in the study area
echo
echo "v.select ainput=slides atype=point binput=slope_units btype=area operator=overlap output=slides_area --o --qq"
v.select ainput=slides atype=point binput=slope_units btype=area operator=overlap output=slides_area --o --qq

# Set mask to sub-area coverd by slope units: we assume landslide
# susceptibility undefined outside of slope units
echo
echo "r.mask vect=slope_units --o --qq"
r.mask vect=slope_units --o --qq

# Rasterize landslide points
echo
echo "v.to.rast input=slides_area output=slides use=val value=1 --o --qq"
v.to.rast input=slides_area output=slides use=val value=1 --o --qq

# Covariates at 10 m resolution already calculated for the slope unit case
echo
echo "v.what.rast map=slides_area raster=slope column=slope --qq"
v.what.rast map=slides_area raster=slope column=slope --qq

# Remove unnecessary columns
columns=idMvt,conf,xsaisi,ysaisi,epsg,num_insee,commune,lieu_dit,typeMvt,libelleTyp,fiabiliteT,libelleFia,PrecDate,libelleDat,prec_xy,libellePre,longitudeD,latitudeDo,date_begin
echo
echo "v.db.dropcolumn map=slides_area columns=$columns --qq"
v.db.dropcolumn map=slides_area columns=$columns --qq

# Double-check that we only work where all maps are defined
echo
echo "r.mapcalc \"somma = slope+pcurv+nthns+easns+geology+pedology+twi+dem_10\" --o --qq"
r.mapcalc "somma = slope+pcurv+nthns+easns+geology+pedology+twi+dem_10" --o --qq

# Cover map needed for random selection of stable points
echo
echo "r.mapcalc \"cover = if(isnull(slides),if(isnull(somma),null(),1),null())\" --o --qq"
r.mapcalc "cover = if(isnull(slides),if(isnull(somma),null(),1),null())" --o --qq

########################### ERRORE! questo e' il numero di slope units positive, non il numero di landslide points!
# Count landslide points
#echo
#echo "nslides=\`db.select -c sql=\"select count(*) from slope_units where slides=1\"\`"
#nslides=`db.select -c sql="select count(*) from slope_units where slides=1"`

# Count landslide points
echo
echo "nslides=\`db.select -c sql=\"select count(*) from slides_area where slope is not null\"\`"
nslides=`db.select -c sql="select count(*) from slides_area where slope is not null"`

# Randomly generate an equal number of non-landslide points with
# fixed seed: multiple runs produce same output
echo
echo "r.random input=dem_10 cover=cover npoints=$nslides seed=666 vector=no_slides --o --qq"
r.random input=dem_10 cover=cover npoints=$nslides seed=666 vector=no_slides --o --qq

echo
echo "v.db.dropcolumn map=no_slides columns=value,covervalue --qq"
v.db.dropcolumn map=no_slides columns=value,covervalue --qq

echo
echo "v.db.addcolumn map=slides_area columns=\'slides integer\' --qq"
v.db.addcolumn map=slides_area columns='slides integer' --qq

echo
echo "v.db.addcolumn map=no_slides columns=\'slides integer\' --qq"
v.db.addcolumn map=no_slides columns='slides integer' --qq

echo
echo "db.execute sql=\"update slides_area set slides=1\""
db.execute sql="update slides_area set slides=1"

echo
echo "db.execute sql=\"update no_slides set slides=0\""
db.execute sql="update no_slides set slides=0"

echo
echo "v.db.dropcolumn map=slides_area columns=slope --qq"
v.db.dropcolumn map=slides_area columns=slope --qq

# Final vector map with landslide AND no-landslide points
echo
echo "v.patch -e input=slides_area,no_slides output=slides_grid --o --qq"
v.patch -e input=slides_area,no_slides output=slides_grid --o --qq

# Upload covariate values to attribute table
echo
echo "v.what.rast map=slides_grid raster=slope column=slope --qq"
v.what.rast map=slides_grid raster=slope column=slope --qq

echo
echo "v.what.rast map=slides_grid raster=relief_3x3 column=relief_3 --qq"
v.what.rast map=slides_grid raster=relief_3x3 column=relief_3 --qq

echo
echo "v.what.rast map=slides_grid raster=relief_5x5 column=relief_5 --qq"
v.what.rast map=slides_grid raster=relief_5x5 column=relief_5 --qq

echo
echo "v.what.rast map=slides_grid raster=relief_7x7 column=relief_7 --qq"
v.what.rast map=slides_grid raster=relief_7x7 column=relief_7 --qq

echo
echo "v.what.rast map=slides_grid raster=relief_9x9 column=relief_9 --qq"
v.what.rast map=slides_grid raster=relief_9x9 column=relief_9 --qq

echo
echo "v.what.rast map=slides_grid raster=twi column=twi --qq"
v.what.rast map=slides_grid raster=twi column=twi --qq

echo "v.what.rast map=slides_grid raster=pcurv column=pcurv --qq"
v.what.rast map=slides_grid raster=pcurv column=pcurv --qq

echo
echo "v.what.rast map=slides_grid raster=nthns column=nthns --qq"
v.what.rast map=slides_grid raster=nthns column=nthns --qq

echo
echo "v.what.rast map=slides_grid raster=easns column=easns --qq"
v.what.rast map=slides_grid raster=easns column=easns --qq

echo
echo "v.what.rast map=slides_grid raster=geology column=geology --qq"
v.what.rast map=slides_grid raster=geology column=geology --qq

echo
echo "v.what.rast map=slides_grid raster=pedology column=pedology --qq"
v.what.rast map=slides_grid raster=pedology column=pedology --qq

columns=cat,slides,slope,relief_3,relief_5,relief_7,relief_9,twi,pcurv,nthns,easns,geology,pedology

echo
echo "db.select sql=\"select ${columns} from slides_grid\" separator=\";\" --qq > susc_grid_gam/input/susc_grid.csv"
db.select sql="select ${columns} from slides_grid where slope is not null" separator=";" --qq > susc_grid_gam/input/susc_grid.csv

#
# export vector layers to predict susceptibility on the whole area
#
r.out.gdal input=slope output=susc_grid_gam/input/slope.gpkg format=GPKG nodata=-9999 --o --qq
r.out.gdal input=relief_9x9 output=susc_grid_gam/input/relief_9.gpkg format=GPKG nodata=-9999 type=Float32 --o -f --qq
r.out.gdal input=twi output=susc_grid_gam/input/twi.gpkg format=GPKG nodata=-9999 type=Float32 --o -f --qq
r.out.gdal input=pcurv output=susc_grid_gam/input/pcurv.gpkg format=GPKG nodata=-9999 --o -f --qq
r.out.gdal input=nthns output=susc_grid_gam/input/nthns.gpkg format=GPKG nodata=-9999 type=Float32 --o -f --qq
r.out.gdal input=easns output=susc_grid_gam/input/easns.gpkg format=GPKG nodata=-9999 type=Float32 --o -f --qq
r.out.gdal input=geology output=susc_grid_gam/input/geology.gpkg format=GPKG type=Float32 --o --qq
#
# run R code!
#
echo
echo "Rscript susc_grid_gam.R &> susc_grid_gam/susc_grid_gam_out.txt"
Rscript susc_grid_gam.R &> susc_grid_gam/susc_grid_gam_out.txt

#
# output layers is found in the susc_grid_gam/output folder
#
# GAM result
echo
echo "r.in.gdal input=susc_grid_gam/output/gampred.gpkg output=tmp --o --qq"
r.in.gdal input=susc_grid_gam/output/gampred.gpkg output=tmp --o --qq

echo
echo "r.mapcalc \"susc_grid_predict_gam = tmp\" --o --qq"
r.mapcalc "susc_grid_predict_gam = tmp" --o --qq

# GLM result
echo
echo "r.in.gdal input=susc_grid_gam/output/glmpred.gpkg output=tmp --o --qq"
r.in.gdal input=susc_grid_gam/output/glmpred.gpkg output=tmp --o --qq

echo
echo "r.mapcalc \"susc_grid_predict_glm = tmp\" --o --qq"
r.mapcalc "susc_grid_predict_glm = tmp" --o --qq

echo
echo "g.remove type=raster name=tmp -f --qq"
g.remove type=raster name=tmp -f --qq

echo
echo "r.mask -r --qq"
r.mask -r --qq

echo
echo " ... Done."
echo 

