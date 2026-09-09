library(terra)

#I like making a view function for spatial vectors
view <- function(x){
  View(as.data.frame(x))
}

#create a function to calculate the mode
Mode <- function(x, na.rm = TRUE){
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}

#read in seabed sample points
v <- vect('D:/GIS/fundy/layers/us_seabed_usgs_one.shp')

#read in OBIA polygons
p <- vect('D:/GIS/Geomorphometry/data/GoM/W00609_segment_1.shp')

#set the crs
p <- project(p, crs(v))

#assign IDs to the polygons
p$ID <- 1:nrow(p)
p_full <- p

#get only points that overlap polygons
v <- crop(v, p)

#check for duplicate lat and longs
dup <-(duplicated(v$Longitude) & duplicated(v$Latitude)) | (duplicated(v$Longitude, fromLast = TRUE) & duplicated(v$Latitude, fromLast = TRUE))

#disregard duplicates that are sediment observations
dup <- v$Facies != 'Sediment' & dup

#remove duplicates
v <- v[!dup,]

#check again
dup <- duplicated(v$Longitude) & duplicated(v$Latitude); sum(dup)
v[dup]

#create a duplicate point with grain size observations
gs <- v[ ,'Grainsze']

#assign the point values to polygons
p <- intersect(p, gs)

#aggregate per polygon
agg <- aggregate(p, by = 'ID', fun = mean, count = FALSE)

#remove "agg" from all column names
names(agg) <- gsub('agg_', '', names(agg))

#remove outlier grain sizes
agg <- agg[abs(agg$Grainsze) < 10,]

library(randomForest)

#predict with rf using all predictors except ID column
rf <- randomForest(Grainsze ~ .-ID, data = agg, ntree = 1000, importance = TRUE)
rf

varImpPlot(rf)

#plot partial response for top 7 predictors
imp <- rownames(rf$importance[order(rf$importance[,1], decreasing = TRUE), ])

par(mfrow = c(2,4))
for (i in 1:7){
  partialPlot(x=rf, pred.data=as.data.frame(agg), x.var=as.character(imp[i]), main = imp[i])
}
partialPlot(rf, agg, 'Grainsze', 'Depth', main = 'Depth')

plot(agg$Grainsze, predict(rf))

#predict rf model at the polygons
pred <- predict(rf, p_full, type = 'response')
p_full$meanGS <- pred

plot(p_full, 'meanGS', col = terrain.colors(100), lwd = 0.5, main = 'Mean grain size (mm)')

#write to disc
writeVector(p_full, 'D:/GIS/Gulf_of_Mexico/layers/meanGS_predict.shp')
writeVector(agg, 'D:/GIS/Gulf_of_Mexico/layers/sediments_agg.shp')
