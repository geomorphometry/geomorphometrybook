#!/usr/bin/env python
# coding: utf-8

# author: Romain Hugonnet
# reference: Simplified code from Geomorphology, Chapter 19, Python section.

# ==== Plotting parameters for nice rendering ====
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 500
plt.rcParams['savefig.dpi'] = 500
plt.rcParams['font.size'] = 9

# ==== Spatial Data Handling ====
from geoutils import Raster, Vector
from xdem import DEM

dem = DEM("../Data/ponui_island_dtm.tif")
outlines = Vector("../Data/ponui_buffer10m.gpkg")

# Only the metadata of raster objects is loaded, while the array will implicitly load only if it is required.
# Metadata can be shown by simply typing the object's name, and a longer summary using `info()`.

dem.info()

# We plot the DEM and vector data using `plot()`

dem.plot(cmap="terrain", cbar_title="Elevation (m)")
outlines.plot(facecolor="none", edgecolor="k")
plt.show()


# We then mask values outside the island by creating a mask from the vector and using `set_mask()`.

mask_outlines = outlines.create_mask(dem)

# As `Raster` objects support Python arithmetic, indexing and interface with **NumPy**, we can thus easily compute the mean of the DEM values outside the mask to verify it is mainly ocean (near zero).

import numpy as np
print(f"Mean elevation outside mask: {np.mean(dem[~mask_outlines]):.1f} m")

dem.set_mask(~mask_outlines)

# We crop the DEM passing bounds manually, but could also use a reference dataset to match:

cropped_dem = dem.crop((dem.bounds.left + 1500, dem.bounds.bottom,
                        dem.bounds.right - 1000, dem.bounds.bottom + 1500))

# ==== Gridding LiDAR Point Clouds ====
# We generate the DEM examplified above from lidar data using PDAL's inverse-distance weighting.

import pdal
input_filename = "../Data/ponui.laz"
output_filename = "../Data/ponui.tif"
json_string = f"""
    [
        "{input_filename}",
        {{
            "type":"writers.gdal",
            "filename": "{output_filename}",
            "resolution": 2.0,
            "output_type":"all"
        }}
    ]
    """
pipeline = pdal.Pipeline(json_string)
_ = pipeline.execute() # Output type "all" is mean/min/max/IDW/count/std


# We open the multi-band output raster and plot the IDW-gridded elevation along with two statistics.

outputs = Raster(output_filename)

fig, ax = plt.subplots(1, 3)
outputs.plot(ax=ax[0], bands=3, cmap="terrain", cbar_title="IDW elevation (m)")
outputs.plot(ax=ax[1], bands=4, cmap="Blues", cbar_title="Point count per cell")
outputs.plot(ax=ax[2], bands=5, cmap="Reds", cbar_title="Standard deviation per cell (m)")
plt.show()

# ==== Deriving Land Surface Parameters ====
# We reproject the DEM to the local UTM with `reproject()` and `get_metric_crs()` to derive reliable terrain attributes.

dem = dem.reproject(crs=dem.get_metric_crs())

# We compute and visualize the difference in slope between the two methods.

slope_h = dem.slope() # Default is "Horn"
slope_zt = dem.slope(method="ZevenbergThorne")
diff = slope_h - slope_zt

fig, ax = plt.subplots(1, 3)
slope_h.plot(ax=ax[0], cmap="Reds", cbar_title="Slope of Horn (°)")
slope_zt.plot(ax=ax[1], cmap="Reds", 
  cbar_title="Slope of Zevenberg and Thorne (°)")
diff.plot(ax=ax[2], cmap="RdBu", cbar_title="Difference (°)", vmin=-1, vmax=1)
plt.show()

# We derive the slope, aspect, hillshade, curvature, topographic position index (TPI), terrain ruggedness index (TRI), roughness and rugosity.

attr_names = ["hillshade", "slope", "aspect", "curvature", 
  "topographic_position_index", "terrain_ruggedness_index", 
  "roughness", "rugosity"]
attrs = cropped_dem.get_terrain_attribute(attr_names)

fig, ax = plt.subplots(4, 2)
cmaps = ["Greys_r", "Reds", "twilight", "RdGy", "RdBu", 
  "Purples", "Oranges", "YlOrRd"]
labels = ["Hillshade", "Slope (°)", "Aspect (°)", "Curvature (100 / m)",
          "TPI (m)", "TRI (m)", "Roughness (m)", "Rugosity"]
vlims = [(None,)*2, (None,)*2, (None,)*2, (-10, 10), (-0.1, 0.1), 
  (0, 5), (0, 5), (1, 3)]
for i in range(8):
    attrs[i].plot(ax=ax.flatten()[i], cmap=cmaps[i], cbar_title=labels[i],
                  vmin=vlims[i][0], vmax=vlims[i][1])
    plt.xticks([])
    plt.yticks([])
plt.tight_layout()
plt.show()
