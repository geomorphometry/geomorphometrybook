

##GISDBASE=[your_path]/datagrass
##LOCATION_NAME=reunion
##MAPSET=PERMANENT

# Always set the computational region!
echo
echo "g.region rast=dem_10 --qq"
g.region rast=dem_10 --qq

# Store file name for values of metrics in a variable & write headers
aucfile=susc_slopeunits_gam/output/output_metrics.txt
rm -f ${aucfile}
echo "Combination, AUC_ROC, Brier Score:" > $aucfile
# Create new empty input, output folders in existing folder susc_slopeunits_gam
rm -rf susc_slopeunits_gam/input
rm -rf susc_slopeunits_gam/output
mkdir susc_slopeunits_gam/input
mkdir susc_slopeunits_gam/output
# Store file name for values of metrics in a variable & write headers
aucfile=susc_slopeunits_gam/output/output_metrics.txt
rm -f ${aucfile}
echo "Combination, AUC_ROC, Brier Score:" > $aucfile

# check if we have null values
columns=`db.select sql="select * from slope_units limit 0" separator=space --qq | cut -f3- -d" "`
echo
for col in ${columns[@]}
do
    nulls=`db.select -c sql="select count(*) from slope_units where ${col} is null" --qq`
    echo "Column: $col; Null values: $nulls"
done
echo

# count number of slides within each slope unit
echo
echo "v.vect.stats point=slides areas=slope_units method=sum count_column=tmp --o --qq"
v.vect.stats point=slides areas=slope_units method=sum count_column=tmp points_column=cat stats_column=dummy --o --qq

v.db.addcolumn map=slope_units column='slides integer' --qq
db.execute sql="update slope_units set slides=0" --qq

# assign "unstable" to each slope unit if number of slides>0 (at least one slide) 
echo
echo "db.execute sql=\"update slope_units set slides=1 where tmp>0\" --qq"
db.execute sql="update slope_units set slides=1 where tmp>0" --qq

v.db.dropcolumn map=slope_units column=tmp,dummy --qq

#columns=`db.select sql="select * from slope_units limit 0" separator=comma --qq | cut -f3- -d","`

columns=cat,slope_average,slope_stddev,pcurv_average,pcurv_stddev,twi_average,twi_stddev,nthns_average,nthns_stddev,easns_average,easns_stddev,perc_geo_1,perc_geo_2,perc_geo_3,perc_geo_4,perc_geo_5,slides

# export data for fit: CSV (text) format
echo
echo "db.select sql=\"select ${columns} from slope_units\" separator=\";\" --qq > susc_slopeunits_gam/input/susc_slopeunits.csv"
db.select sql="select ${columns} from slope_units" separator=";" --qq > susc_slopeunits_gam/input/susc_slopeunits.csv

# export data for fit: GPKG (vecor) format
echo
echo "v.out.ogr -m input=slope_units output=susc_slopeunits_gam/input/slope_units.gpkg format=GPKG --o --qq"
v.out.ogr -m input=slope_units output=susc_slopeunits_gam/input/slope_units.gpkg format=GPKG --o --qq

echo    
echo " -- calculating suscetibility maps -- "
echo

echo
echo "Rscript susc_slopeunits_gam.R &> susc_slopeunits_gam/susc_slopeunits_gam_out.txt"
Rscript susc_slopeunits_gam.R &> susc_slopeunits_gam/susc_slopeunits_gam_out.txt

strings=(gam glm)

for string in ${strings[@]}
do
    echo    
    echo " -- preparing suscetibility map for $string ...."
    echo
    db.droptable table=susc_slopeunits_fit_${string} -f --qq
    db.in.ogr input=susc_slopeunits_gam/output/susc_slopeunits_fit_${string}.csv output=susc_slopeunits_fit_${string} --o    
    v.db.dropcolumn map=slope_units columns=susc_${string}
    v.db.addcolumn map=slope_units columns="susc_${string} real"
    db.execute sql="update slope_units set susc_${string} = (select susc from susc_slopeunits_fit_${string} where SU_ID=slope_units.cat)"
    v.to.rast input=slope_units output=susc_slopeunits_fit_${string} use=attr attribute_column=susc_${string} --o --qq
    #    
done
echo
#
# At this point our mapset "PERMANENT" contains additional maps:

# -> susc_slopeunits_fit_gam (raster)
# -> susc_slopeunits_fit_glm (raster)
#
# load workspace file fig03a.gxw to generate Fig. 3(a) of chapter 23 in bw
# load workspace file fig03b.gxw to generate Fig. 3(b) of chapter 23 in bw
# load workspace file fig03c.gxw to generate Fig. 3(c) of chapter 23 in bw
# load workspace file fig03d.gxw to generate Fig. 3(d) of chapter 23 in bw
