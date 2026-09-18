#Read rasters from disk into memory
dem = readmap("dem.map")
drainage = readmap("drainage.map")
flowdir = readmap("ldd.map")
#Give every cell of the drainage raster a unique nominal value
drainage_id = nominal(uniqueid(drainage))
#Calculate the catchment of each of the drainageID cells
catchments = subcatchment(flowdir,drainage_id)
#Calculate the minimum elevation in each catchment
drainage_z = areaminimum(dem,catchments)
#Calculate HAND by subtracting drainageZ from DEM
hand = dem - drainage_z
#Write the result to disk
report(hand,"hand.map")
