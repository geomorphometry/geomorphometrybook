using Pkg
Pkg.activate(".")

# ==== SET INPUT FILE PATHS ====
laz_fn = abspath(joinpath(@__DIR__, "../Data/ponui.laz")) # Path to lidar points
dsm_fn = abspath(joinpath(@__DIR__, "../Data/ponui_island_dsm.tif")) # Path to DSM raster
dtm_fn = abspath(joinpath(@__DIR__, "../Data/ponui_island_dtm.tif")) # Path to DTM raster

# ==== Spatial Data Handling ====
## We use the LazIO.jl package to open LiDAR point cloud data
using LazIO
ds = LazIO.open(laz_fn)
# We can subset the first point
p = ds[1]  # indexing starts with 1 in Julia

# Interfaces
## We use the GeoInterface.jl package to work with spatial geometries. For example, we can use it to examine properties of the data.
using GeoInterface

isgeometry(ds)  # true
isgeometry(p)  # true
geomtrait(ds)  # MultiPointTrait
geomtrait(p)  # PointTrait
ncoord(p)  # 3
getcoord(p, 1)  # 1.79344255e6
GeoInterface.x(p)  # 1.79344255e6
GeoInterface.crs(ds)  # nothing (LazIO currenlty cannot read in crs automatically)

using GeoFormatTypes # For crs and projections
crs = GeoFormatTypes.EPSG(2193, 7839); # define a crs based on EPSG codes

## We can convert ds to a data frame and write it to a GIS vector file (geopackage) along with the appropriate CRS
using GeoDataFrames
using DataFrames
df = DataFrame(ds)  # can take a while
GeoDataFrames.write("pc.gpkg", first(df, 100); crs)  # Avoid writing all points


# Plotting
## We can load the CairoMakie.jl package for plotting
using CairoMakie
CairoMakie.activate!(type="png")
CairoMakie.set_theme!()

## Define a custom plotting function that includes a color colorbar
"""Plot with automatic colorbar."""
function plotcb(args...; kwargs...)
    fig, _, plt = plot(args...; kwargs...)
    Colorbar(fig[1, 2], plt)
    fig
end

## We plot a subset of the points using indexing
@time thinned = ds[1:100_000:length(ds)];
plotcb(thinned, zscale=5, colorrange=(0, 50))

# ==== Gridding LiDAR Point Clouds ====
## We can use a spatial index to store a which points fall in each raster cell and then apply a reducer function (e.g. min, mean, max, etc.) to determine a value for that cell based on the values of the points within that cell.

using PointCloudRasterizers, Extents
dsc = collect(ds)  # Load pointcloud into memory instead of rereading it each time.
cellsizes = (1.0, 1.0)  # rasterize into 1 x 1m
ex = Extent(X=(1.794519e6, 1.79552e6), Y=(5.91424475e6, 5.91524575e6))
@time pci = index(dsc, cellsizes; bbox=ex, crs)  # First index the pointcloud

using Statistics
cga = counts(pci)
## Check the average density of the filled (containing at least 1 point) cells
filter(>=(1), cga) |> mean |> round  # 6.0
plotcb(cga, colormap=:thermal, colorrange=(0, 10))

first_return(p) = return_number(p) == 1  # this defines a new function
## Rather than a summary of all points we will define a surface based on the value of the first LiDAR beam return.
first_return_pci = filter(pci, first_return)
raster = reduce(first_return_pci, reducer=median)
plotcb(raster, colorrange=(0, 100))

## We will use the Geomorphometry package for geomorphological analyses of elevation surfaces and the GeoArrays.jl package for handling spatial raster data. Alternatively we could use the newer Rasters.jl package for handling spatial raster data.

## Here we will create a surface and split it into terrain and non-terrain by defining a threshold surface using a Progressive Morphological Filter (PMF). All point below the PMF surface are considered terrain whereas those above are considered non-terrain (e.g. vegetation).

using Geomorphometry
using GeoArrays
raster = reduce(pci, reducer=minimum) # Overwrite object `raster` now as the minimum value in cell
craster = GeoArrays.coalesce(raster, Inf) # Replace missing values with Inf
fraster, _ = pmf(craster, ωₘ=25.0, slope=10 / 1000, dh₀=0.5) # Define a threshold surface using PMF

function below_threshold(p, raster_value)
    GeoInterface.z(p) <= raster_value
end # define function to identify points below threshold surface

n = filter(pci, fraster, below_threshold) # filter for points below threshold
dtm = reduce(n, reducer=median)  # Grid to DTM based on median of retained points
plotcb(dtm, colorrange=(0, 100))

## We can use GeoStats.jl to interpolate gaps in the surface
using GeoStats

## Here we compare a DTM created using our PMF procedure to a DTM created using only points classified as "ground" in the original data. We interpolate any gaps using inverse distance weighting with an exponent of 2 and compare the differences.

ground(p) = classification(p) == LazIO.classes.ground # Function to determine if a point is classified as "ground"
ground_pci = filter(pci, ground)
cdtm = reduce(ground_pci, reducer=median)
GeoArrays.fill!(cdtm, IDW(2), maxneighbors=10, neighborhood=MetricBall(10))
GeoArrays.fill!(dtm, IDW(2), maxneighbors=10, neighborhood=MetricBall(10))
diff = dtm - cdtm
display(plotcb(dtm, colorrange=(0, 100)));
display(plotcb(cdtm, colorrange=(0, 100)));
display(plotcb(diff, colormap=:delta, colorrange=(-5, 5)));

## Alternatively we could use the Point Data Abstraction Library (PDAL) to create a DTM. Here's how to load PDAL and get some metadata about the file.
using PDAL_jll
run(`$(pdal()) info --summary $laz_fn`)

# ==== Deriving Land Surface Parameters ====
dsm = GeoArrays.read(dsm_fn) #Read in DSM raster
sub = crop(GeoArrays.coalesce(dsm, 0.0), ex) # Crop raster

dtm = GeoArrays.read(dtm_fn) # Read in DTM raster
dtm = GeoArrays.warp(dtm, dsm) # warp DTM to DSM grid
sub = crop(GeoArrays.coalesce(dtm, 0.0), ex) # crop

display(plotcb(slope(sub, method=Horn()), colormap=:viridis)); # slope
display(plotcb(aspect(sub), colormap=:phase)); # aspect
display(plotcb(curvature(sub), colormap=:curl, colorrange=(-25, 25))); # curvature

acc, dir = flowaccumulation(sub, method=D8()) # flow accumulation

# Terrain Visualization
## Three shading methods to visualize terrain
display(plotcb(hillshade(sub), colormap=:greys,), colorrange=(0, 255)); # hillshade
display(plotcb(multihillshade(sub), colormap=:greys,), colorrange=(0, 255)); #multihillshade
display(plotcb(pssm(sub), colormap=Reverse(:greys), colorrange=(0, 90),)); # Perceptually Shaded Slope Map
