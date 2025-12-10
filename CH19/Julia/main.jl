# REQUIRED TO SET INPUT FILE PATHS
laz_fn = abspath(joinpath(@__DIR__, "../../data/ponui.laz"))
dsm_fn = abspath(joinpath(@__DIR__, "../../data/ponui_island_dsm.tif"))
dtm_fn = abspath(joinpath(@__DIR__, "../../data/ponui_island_dtm.tif"))

# Spatial Data Handling
using LazIO
ds = LazIO.open(laz_fn)
p = ds[1]  # indexing starts with 1 in Julia

## Interfaces
using GeoInterface

isgeometry(ds)  # true
isgeometry(p)  # true
geomtrait(ds)  # MultiPointTrait
geomtrait(p)  # PointTrait
ncoord(p)  # 3
getcoord(p, 1)  # 1.79344255e6
GeoInterface.x(p)  # 1.79344255e6
GeoInterface.crs(ds)  # nothing

using GeoFormatTypes
crs = GeoFormatTypes.EPSG(2193, 7839);

using GeoDataFrames
using DataFrames
df = DataFrame(ds)
GeoDataFrames.write("pc.gpkg", first(df, 100); crs)  # Avoid writing all points


## Plotting
using CairoMakie
CairoMakie.activate!(type="png")
CairoMakie.set_theme!()

"""Plot with automatic colorbar."""
function plotcb(args...; kwargs...)
    fig, _, plt = plot(args...; kwargs...)
    Colorbar(fig[1, 2], plt)
    fig
end

@time thinned = ds[1:100_000:length(ds)];
plotcb(thinned, zscale=5, colorrange=(0, 50))


# Gridding LiDAR Point Clouds
using PointCloudRasterizers, Extents
dsc = collect(ds)  # Load pointcloud into memory instead of rereading it each time.
cellsizes = (1.0, 1.0)  # rasterize into 1 x 1m
ex = Extent(X=(1.794519e6, 1.79552e6), Y=(5.91424475e6, 5.91524575e6))
@time pci = index(dsc, cellsizes; bbox=ex, crs)  # First index the pointcloud

using Statistics
cga = counts(pci)
# Check the average density of the filled (containing at least 1 point) cells
@info filter(>=(1), cga) |> mean |> round  # 6.0
plotcb(cga, colormap=:thermal, colorrange=(0, 10))

first_return(p) = return_number(p) == 1  # this defines a new function
first_return_pci = filter(pci, first_return)
raster = reduce(first_return_pci, reducer=median)
plotcb(raster, colorrange=(0, 100))

using Geomorphometry
using GeoArrays
raster = reduce(pci, reducer=min)
craster = GeoArrays.coalesce(raster, Inf)
fraster, _ = pmf(craster, ωₘ=25.0, slope=10 / 1000, dh₀=0.5)

function below_threshold(p, raster_value)
    GeoInterface.z(p) <= raster_value
end # define function to identify points below threshold surface

n = filter(pci, fraster, below_threshold)
dtm = reduce(n, reducer=median)
plotcb(dtm, colorrange=(0, 100))

using GeoStats
ground(p) = classification(p) == LazIO.classes.ground
ground_pci = filter(pci, ground)
cdtm = reduce(ground_pci, reducer=median)
GeoArrays.fill!(cdtm, IDW(2), maxneighbors=10, neighborhood=MetricBall(10))
GeoArrays.fill!(dtm, IDW(2), maxneighbors=10, neighborhood=MetricBall(10))
diff = dtm - cdtm
display(plotcb(dtm, colorrange=(0, 100)));
display(plotcb(cdtm, colorrange=(0, 100)));
display(plotcb(diff, colormap=:delta, colorrange=(-5, 5)));

using Pkg
Pkg.add("PDAL_jll")  # or ] add PDAL_jll
using PDAL_jll
run(`$(pdal()) info $laz_fn`)


## Deriving Land Surface Parameters
using GeoArrays
dsm = GeoArrays.read(dsm_fn)
sub = crop(GeoArrays.coalesce(dsm, 0.0), ex)

dtm = GeoArrays.read(dtm_fn)
dtm = GeoArrays.warp(dtm, dsm)
sub = crop(GeoArrays.coalesce(dtm, 0.0), ex)

display(plotcb(slope(sub, method=Horn()), colormap=:viridis));
display(plotcb(aspect(sub), colormap=:phase));
display(plotcb(curvature(sub), colormap=:curl, colorrange=(-25, 25)));

using Geomorphometry: flowaccumulation
acc, dir = flowaccumulation(sub, method=D8())


## Terrain Visualization
using Geomorphometry: hillshade, multihillshade, pssm
display(plotcb(hillshade(sub), colormap=:greys,), colorrange=(0, 255));
display(plotcb(multihillshade(sub), colormap=:greys,), colorrange=(0, 255));
display(plotcb(pssm(sub), colormap=Reverse(:greys), colorrange=(0, 90),));
