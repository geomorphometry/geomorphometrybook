#load required packages
library(MultiscaleDTM)
library(terra)

#load in the DTM dataset
r <- rast('D:/GIS/Geomorphometry/layers/ponui_dtm_setnull.tif')

#plot the elevation raster
plot(r)

#use Qfit() from MultiscaleDTM to calculate quadratic surface attributes at two different scales
#including defaults "elev", "qslope", "qaspect", "qeastness", "qnorthness", "profc", "planc", "twistc", "meanc", "maxc", "minc", "features"
q1 <- Qfit(r)
q13 <- Qfit(r, w=13)

#min-max normalize terrain attributes
nx1 <- minmax(q1)
q1n <- (q1 - nx1[1,]) / (nx1[2,] - nx1[1,])

nx13 <- minmax(q13)
q13n <- (q13 - nx13[1,]) / (nx13[2,] - nx13[1,])

#save terrain attribute rasters to disc
writeRaster(q1n, paste0('D:/GIS/Geomorphometry/layers/', names(q13), '_1.tif'))
writeRaster(q13n, paste0('D:/GIS/Geomorphometry/layers/', names(q13), '_13.tif'))

#calculated adjusted standard deviation attribute using AdjSD() at two scales
sD1 <- AdjSD(r)
SD13 <- AdjSD(r, w=13)

#min-max normalize
nx1 <- minmax(sD1)
sD1n <- (sD1 - nx1[1,]) / (nx1[2,] - nx1[1,])

nx13 <- minmax(SD13)
SD13n <- (SD13 - nx13[1,]) / (nx13[2,] - nx13[1,])

#save rasters to disc
writeRaster(sD1n, paste0('D:/GIS/Geomorphometry/layers/', names(sD1), '_1.tif'))
writeRaster(SD13n, paste0('D:/GIS/Geomorphometry/layers/', names(SD13), '_13.tif'))

#calculate topographic position index using TPI() function at two scales
tpi1 <- TPI(r)
tpi13 <- TPI(r, w=13)

#min-max normalize
nx1 <- minmax(tpi1)
tpi1n <- (tpi1 - nx1[1,]) / (nx1[2,] - nx1[1,])

nx13 <- minmax(tpi13)
tpi13n <- (tpi13 - nx13[1,]) / (nx13[2,] - nx13[1,])

#save rasters to disc
writeRaster(tpi1n, paste0('D:/GIS/Geomorphometry/layers/', names(tpi1), '_1.tif'))
writeRaster(tpi13n, paste0('D:/GIS/Geomorphometry/layers/', names(tpi13), '_13.tif'))

#calculate deviation from the mean value with DMV() function at two scales
dmv1 <- DMV(r)
dmv13 <- DMV(r, w=13)

#min-max normalize
nx1 <- minmax(dmv1)
dmv1n <- (dmv1 - nx1[1,]) / (nx1[2,] - nx1[1,])

nx13 <- minmax(dmv13)
dmv13n <- (dmv13 - nx13[1,]) / (nx13[2,] - nx13[1,])

#save rasters to disc
writeRaster(dmv1n, paste0('D:/GIS/Geomorphometry/layers/', names(dmv1), '_1.tif'))
writeRaster(dmv13n, paste0('D:/GIS/Geomorphometry/layers/', names(dmv13), '_13.tif'))

#select layers for unsupervised classification
lyr_names <- c('adjSD_13', 'dmv_13', 'elev_1', 'meanc_13', 'planc_13', 'profc_13', 'qslope_13', 'twistc_13')

#load selected rasters
stack <- rast(
  paste0('D:/GIS/Geomorphometry/layers/', lyr_names, '.tif')
)

#rename to match layer names
names(stack) <- lyr_names

#perform PCA with the terra function
pca <- prcomp(stack, maxcell = 10000000, scale. = TRUE)

#calculate variance explained for each component
pca$sdev^2 / sum(pca$sdev^2)

#calculate cumulative variance explained
cumsum(pca$sdev^2 / sum(pca$sdev^2))

#the first 6 components explain 95% of variance
#predict the first 6 principal components spatially and plot
p <- predict(stack, pca, index = 1:6)
plot(p)

#test different values of k for kmeans clustering using a subset of the data
r_val <- values(p, na.rm = TRUE)
n = 1000000 #sample a subset for processing time
r_val <- r_val[sample(1:nrow(r_val), n), ]

#loop through 2:10 clusters
l <- list()
for(k in 2:10){
  print(k)
  kmeans <- kmeans(r_val, centers = k, nstart = 10)
  df <- data.frame(k = k, bss = kmeans$betweenss, totwss = kmeans$tot.withinss)
  l[[length(l) + 1]] <- df
}
l <- do.call(rbind, l)

#plot within-cluster sum of squares vs number of clusters
plot(l$k, l$totwss, type = 'l')

#elbow test
library(ggplot2)

ggplot(l, aes(x = k, y = totwss)) +
  geom_line() +
  geom_point() + 
  labs(x = 'Number of clusters', y = 'Total WSS') +
  theme_minimal() +
  theme(
    panel.border = element_blank(), # Ensures no full border
    axis.line = element_line(color = "black") # Add axis lines
  )

#save plot with background
ggsave('D:/GIS/Geomorphometry/out/elbow.tif', width = 3, height = 3, dpi = 300)

#run the full kmeans with selected number of clusters
r_val <- values(p, na.rm = TRUE)
kmeans <- kmeans(r_val, centers = 4, nstart = 10)

#set the values of the raster to the cluster results
clust <- p[[1]]
values(clust)[!is.na(values(clust))] <- kmeans$cluster
plot(clust)

writeRaster(clust, 'D:/GIS/Geomorphometry/layers/kmeans4_PCA6.tif')
