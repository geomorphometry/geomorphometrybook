#!/usr/bin/env python3

##############################################################################
# MODULE:    geomorphometry_in_grass.py
#
# AUTHOR(S): Corey T. White <ctwhite48@gmail.com>
#            Helena Mitasova <>
#            Markus Neteler <>
#            Anna Petrasova <>
#            Jaroslav Hofierka <>
#
# PURPOSE:   This script supplements the chapter "Geomorphometry in GRASS"
#            from the Geomorphometry book and generates the data sets presented
#            there for Ponui Island. This script has been worked out with
#            GRASS 8.5.
#
# COPYRIGHT: (C) 2025 by Corey T. White, Helena Mitasova, Markus Neteler,
#            Anna Petrasova, Jaroslav Hofierka and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################


from pathlib import Path
import os
import subprocess
import sys
from io import StringIO
from PIL import Image
import matplotlib.pyplot as plt

# Configuration
PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_NAME = Path(PROJECT_DIR, "ponui")
MAPSET_NAME = "PERMANENT"

DSM_PATH = Path(PROJECT_DIR, "data/dsm.cog.tif")
DSM_NAME = "dsm_10m"

DTM_PATH = Path(PROJECT_DIR, "data/dtm.cog.tif")
DTM_NAME = "dem_10m"
DTM_RELIEF = "dtm_relief"

ISLAND_RESOLUTION = 10  # meters

LIDAR_PATH = Path(PROJECT_DIR, "data/lidar.laz")
LIDAR_DTM_10M = "lidar_dtm_10m"
LIDAR_DTM_1M = "lidar_dtm_1m"
LIDAR_DTM_1M_RELIEF = "lidar_dtm_1m_relief"
LIDAR_DTM_1M_SKYVIEW = "lidar_dtm_1m_skyview"

AOI_REGION = "aoi"
AOI_RESOLUTION = 1  # meters
SAVE_DIR = Path(PROJECT_DIR, "figures")

COLOR_OCEAN = "#0F78BE"


def save_jpeg(image: Image.Image, output_path: Path) -> None:
    try:
        # Open the image
        with Image.open(image) as im:
            # Check if the image has an alpha channel and convert to RGB
            if im.mode in ("RGBA", "P"):
                # im = im.convert("RGB", dither=None)
                # White matches the background of map grid
                background = Image.new('RGB', im.size, color=(255, 255, 255))
                background.paste(im, mask=im.split()[3])
                background.save(
                    output_path,
                    "JPEG",
                    dpi=(300, 300),
                    quality=100,
                    dither=None
                )
            # Save the image with 300 DPI specified in the metadata
            # For JPEG format
            else:
                im.convert('RGB').save(
                    output_path,
                    "JPEG",
                    dpi=(300, 300),
                    quality=100
                )

            print(f"Image successfully saved to {output_path} with 300 DPI.")

    except FileNotFoundError:
        print(f"Error: The file '{output_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    v = sys.version_info
    print(f"We are using Python {v.major}.{v.minor}.{v.micro}")
    sys.path.append(
        subprocess.check_output(
            ["grass", "--config", "python_path"], text=True
        ).strip()
    )

    # Create output directory if it doesn't exist
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Import GRASS libraries
    import grass.script as gs
    import grass.jupyter as gj
    from grass.tools import Tools
    from grass.exceptions import CalledModuleError, ScriptError
    import numpy as np

    def full_region_map_figure(
            tools: Tools,
            map_name: str,
            relief: str,
            legend_units: str = "",
            legend_flags: str = "bt"
    ) -> gj.Map:
        univar_json = tools.r_univar(map=map_name, format="json").json
        figure_output = Path(SAVE_DIR, f"{map_name}")
        print(f"Saving AOI map figure to {figure_output}")
        m = gj.Map(width=800, use_region=True)
        m.d_rast(map="ocean")
        m.d_grid(
            size="00:01:10",
            color="#FDFDFD",
            fontsize=22,
            text_color="#FDFDFD",
            border_color="#FFFFFF",
            flags="ga",
        )
        m.d_shade(color=map_name, shade=relief, flags="n")
        # m.d_vect(map="grid_1k_1k", type="boundary", color="#FDFDFD", width=1)

        # m.d_grid(
        #     size="1000",
        #     color="#FDFDFD",
        #     fontsize=16,
        #     text_color="#FDFDFD",
        #     border_color="#FDFDFD",
        #     flags="ad",
        # )
        highlight = ("#1F78B4", "#7B3294", "#E66101")
        m.d_vect(map=AOI_REGION, type="boundary", color=highlight[2], width=3)
        m.d_text(
            text="Oranga Bay",
            at=(34, 53),
            size=2.25,
            color="#FDFDFD",
            font="Fira Sans Condensed Bold"
        )
        m.d_legend(
            raster=map_name,
            at="4,21,82,85",
            font="Fira Sans Condensed Light",
            fontsize=24,
            border_color="#FDFDFD",
            bgcolor=COLOR_OCEAN,
            color="#FDFDFD",
            units=legend_units,
            range=f"{univar_json['min']},{univar_json['max']}",
            flags=legend_flags,
        )
        m.d_barscale(
            at=(1, 4),
            bgcolor="none",
            style="line",
            length=2,
            units="kilometers",
            color="#FDFDFD",
            font="Fira Sans Condensed Light",
            fontsize=24,
            flags="n",
        )

        save_jpeg(m.filename, f"{figure_output}.jpg")
        m.save(filename=f"{figure_output}.png")
        return m

    def _get_symmetric_range(tools, map_name: str) -> float:
        """Return symmetric half-range based on min/max of map (max(|min|, |max|))."""
        stats = tools.r_univar(map=map_name, format="json").json
        vmin = float(stats["min"])
        vmax = float(stats["max"])
        return max(abs(vmin), abs(vmax))

    def aoi_map_figure(
        tools: Tools,
        map_name: str,
        relief: str,
        legend: str | None = None,
        legend_units: str = "",
        legend_title: str = "",
        legend_flags: str = "t",
        # legend_at: str = "10,38,15,20",  #  At region
        legend_at: str = "5,10,20,80",  #  s="s-250"
        # legend_at: str = "45,90,86,91",  # e="e+350"
        legend_range_min: float | None = None,
        legend_range_max: float | None = None,
        shade_flags: str = "n",
        extra_save_name: str | None = None,
        extra_rasters: list[dict] | None = None,
        extra_vectors: list[dict] | None = None,
        extra_shades: list[dict] | None = None,
    ) -> gj.Map:

        save_name = f"{extra_save_name}_aoi" if extra_save_name else f"{map_name}_aoi"
        figure_output = Path(SAVE_DIR, save_name)
        univar_json = tools.r_univar(map=map_name, format="json").json
        _range_min = legend_range_min if legend_range_min is not None else univar_json['min']
        _range_max = legend_range_max if legend_range_max is not None else univar_json['max']
        legend_range = f"{_range_min},{_range_max}"
        print(f"Saving AOI map figure to {figure_output}")

        with gs.RegionManager(region=AOI_REGION, s="s-200", raster=LIDAR_DTM_1M, res=AOI_RESOLUTION, flags="a"):
            m = gj.Map(width=800, use_region=True)
            m.d_rast(map="ocean")

            # Additional shades
            if extra_shades:
                for shade in extra_shades:
                    m.d_shade(**shade)

            m.d_shade(color=map_name, shade=relief, flags=shade_flags)

            # Additional rasters
            if extra_rasters:
                for rast in extra_rasters:
                    m.d_rast(**rast)

            # Additional vectors
            if extra_vectors:
                for vec in extra_vectors:
                    m.d_vect(**vec)

            m.d_grid(
                size="00:00:10",
                color="#FDFDFD",
                text_color="#FDFDFD",
                fontsize=16,
                flags="gac",
            )
            m.d_text(
                text="Oranga Bay",
                at=(20, 84),
                size=4,
                color="white",
                font="Fira Sans Condensed Bold"
            )

            legend_map = legend if legend else map_name

            m.d_legend(
                raster=legend_map,
                at=legend_at,
                font="Fira Sans Condensed Light",
                fontsize=21,
                border_color="none",
                title=legend_title if legend_title != "" else "",
                title_fontsize=24,
                # units=legend_units if legend_units != "" else f" {legend_units}",
                range=legend_range,
                flags=legend_flags,
            )
            m.d_barscale(
                at=(60, 22),
                font="Fira Sans Condensed Light",
                fontsize=21,
                length=250,
                bgcolor="none",
                style="line",
                color="#FDFDFD",
                flags="n",
            )
            save_jpeg(m.filename, f"{figure_output}.jpg")
            m.save(filename=f"{figure_output}.png")
            return m

    def install_grass_addons():
        """
        Install required GRASS addons from the gextensions file in parallel.
        """
        print("Installing GRASS addons:")
        try:
            extensions_path = Path(PROJECT_DIR, "gextensions.txt")
            with extensions_path.open() as f:
                exts = [
                    line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")
                ]

            if not exts:
                print("No extensions listed in gextensions.txt.")
                return

            failed = []
            for ext in exts:
                print(f"\tInstalling {ext}...")
                try:
                    tools = Tools()
                    tools.g_extension(extension=ext, quiet=True)
                except CalledModuleError as e:
                    print(f"Error installing {ext}: {e}")
                    failed.append(ext)

            if failed:
                print(f"Failed to install extensions: {', '.join(failed)}")
                sys.exit(1)

        except FileNotFoundError:
            print("gextensions file not found.")
            sys.exit(1)

    def set_ocean_to_null(elevation_map: str) -> None:
        """Set ocean values (below 0) to NULL in the elevation map."""
        print("Setting ocean values to NULL...")
        tools.r_null(
            map=elevation_map,
            setnull="-9999-0",
            quiet=True
        )

    def create_ocean_background():
        # Create ocean background map
        tools.r_mapcalc(expression="ocean = 1")
        ocean_colors = [(1, COLOR_OCEAN)]
        ocean_color_scheme = "\n".join(
            f"{pos} {color}" for pos, color in ocean_colors
        ) + "\n"
        tools.r_colors(map="ocean", rules=StringIO(ocean_color_scheme))

        tools.r_random_surface(
            output="ocean_uniform",
            high=100,
            distance=2,
            exponent=2.0
        )
        tools.r_surf_gauss(output="ocean_gauss", mean=0, sigma=0.5, seed=3)
        random_ocean_colors = [
            ("0%",   "#FDFDFD"),
            ("0%",   "#7f7d63"),
            ("33%",  "#194438"),
            ("66%",  "#223934"),
            ("100%", "#192b2f"),
        ]
        random_ocean_color_scheme = (
            "\n".join(f"{pos} {color}" for pos, color in random_ocean_colors) + "\n"
        )
        tools.r_colors(
            map="ocean_uniform",
            rules=StringIO(random_ocean_color_scheme)
        )
        tools.r_colors(
            map="ocean_gauss",
            rules=StringIO(random_ocean_color_scheme)
        )

    def brown_elev_color_scheme(tools: Tools, map_name: str) -> None:
        """Apply brown color scheme to elevation map."""
        print("Applying brown elevation color scheme...")
        elev_color_palette = [
            ("0%",   "#F5F5DC"),
            ("25%",  "#CDBEA1"),
            ("50%",  "#9A7B4F"),
            ("75%",  "#4B371C"),
            ("100%", "#2E1503"),
        ]
        # Convert palette list to rules string for r_colors
        elev_color_scheme = "\n".join(
            f"{pos} {color}" for pos, color in elev_color_palette
        ) + "\n"
        tools.r_colors(
            map=map_name,
            rules=StringIO(elev_color_scheme),
            flags=""
        )

    def pounui_island_color_scheme(tools: Tools, map_name: str) -> None:
        """Apply Ponui Island color scheme to elevation map."""
        print("Applying Ponui Island elevation color scheme...")
        ponui_palette = [
            ("0%", "#f3e7d3"),
            ("10%", "#d8cfac"),
            ("20%", "#b4c88a"),
            ("35%", "#82b66a"),
            ("50%", "#4f9d53"),
            ("65%", "#2e7a42"),
            ("80%", "#1f5631"),
            ("90%", "#17483b"),
            ("100%", "#0d3a3a")
        ]
        ponui_colors = "\n".join(
            f"{pos} {color}" for pos, color in ponui_palette
        ) + "\n"
        tools.r_colors(map=map_name, rules=StringIO(ponui_colors), flags="")

    def twi_color_scheme(tools: Tools, map_name: str) -> None:
        """Apply TWI blue-green color scheme."""
        twi_blue_green = [
            ("0%", "#8c510a"),
            ("20%", "#bf812d"),
            ("40%", "#dfc27d"),
            ("55%", "#f6e8c3"),
            ("70%", "#c7eae5"),
            ("85%", "#5ab4ac"),
            ("100%", "#01665e"),
        ]
        twi_colors = (
            "\n".join(f"{pos} {color}" for pos, color in twi_blue_green) + "\n"
        )
        tools.r_colors(map=map_name, rules=StringIO(twi_colors), flags="e")

    def brown_contour_color_scheme(tools: Tools, map_name: str) -> None:
        """Apply brown color scheme to elevation map."""
        print("Applying brown elevation color scheme...")
        elev_color_scheme = """
        0%   #F5F5DC
        25%  #CDBEA1
        50%  #9A7B4F
        75%  #4B371C
        100% #2E1503
        """
        tools.v_colors(
            map=map_name,
            use="attr", column="level",
            rules=StringIO(elev_color_scheme),
            flags="n"
        )

    def resample_dem(
            tools: Tools,
            input: str,
            resolutions: list[float]
    ) -> None:
        """Resample DSM and DTM to target resolutions."""
        for res in resolutions:
            with gs.RegionManager(res=res, flags="a"):
                resampled_name = f"{input}_{int(res)}m"
                try:
                    tools.r_resamp_interp(
                        input=input,
                        output=resampled_name,
                        method="bilinear",
                        quiet=True
                    )
                except CalledModuleError as e:
                    print(f"Error resampling to {res}m: {e}")
                    sys.exit(1)

            # Save and display the resampled map
            m = gj.Map(use_region=False)
            m.d_rast(map="ocean")
            m.d_rast(map=resampled_name)
            m.d_region_grid(raster=resampled_name, flags="")
            m.save(filename=f"{SAVE_DIR}/{resampled_name}.png")

    def import_dem_data(tools: Tools, res: float) -> None:
        """Import DSM and DTM data into GRASS at specified resolution."""
        print(f"Importing DSM and DTM data at {res}m...")
        try:
            # Import DSM
            tools.r_import(
                input=DSM_PATH,
                output=DSM_NAME,
                resample="bilinear",
                resolution="value",
                resolution_value=res,
                title=f"Ponui Island {res}m DSM",
                quiet=True,
            )

            # Import DEM
            tools.r_import(
                input=DTM_PATH,
                output=DTM_NAME,
                resample="bilinear",
                resolution="value",
                resolution_value=res,
                title=f"Ponui Island {res}m DSM",
                quiet=True,
            )

            print("Importing LiDAR data and creating mean DTM...")
            # Import LIDAR data and create DTM
            tools.r_in_pdal(
                input=LIDAR_PATH,
                output=LIDAR_DTM_10M,
                method="mean",
                resolution=res,
                class_filter="2",
                flags="we",
                quiet=True
            )
        except Exception as e:
            print(f"Error importing data: {e}")
            sys.exit(1)

    def process_lidar_data(tools: object) -> None:
        """Import LIDAR data and create DTM using RST method."""
        print("Importing LiDAR data...")
        tools.v_in_pdal(
            input=LIDAR_PATH,
            output="lidar_be_aoi",
            class_filter="2",  # ground points
            flags="or"
        )

    def optimize_rst_params(tools: Tools, points) -> None:

        # Interpolate LiDAR ground points to create DTM using RST
        # Only within the AOI region at 1m resolution
        with gs.RegionManager(
            region=AOI_REGION,
            res=AOI_RESOLUTION,
            flags="a"
        ):
            """Optimize RST parameters using cross-validation."""
            print("Finding optimal RST parameters using cross-validation...")
            results = tools.v_surf_rst_cv(
                point_cloud=points,
                tension=[10, 40, 150, 500],
                smooth=[0.2, 0.5, 1.0, 2.0],
                cv_prefix="cv",
                format="json",
                nprocs=6,
                output_file=Path(PROJECT_DIR, "config/cv_results.json"),
            ).json

            # Sort RMSE by lowest value (Best first)
            sorted_results = results.sort(key=lambda item: item["rmse"])
            fig, ax = plt.subplots(figsize=(10, 6))
            # Extract numeric values robustly
            tensions = []
            smooths = []
            rmses = []
            for item in results:
                try:
                    tval = float(item.get("tension"))
                    sval = float(item.get("smooth"))
                    rval = item.get("rmse")
                    rval = float(rval) if rval not in (None, "") else np.nan
                except Exception:
                    continue
                tensions.append(tval)
                smooths.append(sval)
                rmses.append(rval)

            tensions = np.array(tensions)
            smooths = np.array(smooths)
            rmses = np.array(rmses, dtype=float)

            # Scatter: tension (x), smoothing (y), RMSE encoded by color
            sc = ax.scatter(
                tensions,
                smooths,
                c=rmses,
                cmap="plasma",
                s=80,
                edgecolor="k",
                linewidth=0.5,
                alpha=0.95,
            )

            cbar = fig.colorbar(sc, ax=ax)
            cbar.set_label("RMSE")

            ax.set_xlabel("Tension")
            ax.set_ylabel("Smoothing")
            ax.set_title("RST cross-validation: tension vs smoothing (RMSE color)")

            # Log-scale x-axis (tension spans orders of magnitude)
            try:
                ax.set_xscale("log")
            except Exception:
                pass

            # Highlight best (lowest RMSE) if available
            if rmses.size > 0 and not np.all(np.isnan(rmses)):
                best_idx = int(np.nanargmin(rmses))
                bx, by, br = tensions[best_idx], smooths[best_idx], rmses[best_idx]
                ax.scatter([bx], [by], s=220, facecolors="none", edgecolors="red", linewidths=2)
                ax.annotate(
                    f"best\nRMSE={br:.3f}",
                    xy=(bx, by),
                    xytext=(10, 10),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                )

            ax.grid(True, linestyle="--", alpha=0.4)
            plt.tight_layout()

            out_path = Path(SAVE_DIR, "rst_cv_results.png")
            fig.savefig(out_path, dpi=150)
            print(f"Saved RST CV plot to {out_path}")
            optimized_params = min(results, key=lambda x: x["rmse"])
            print(f"""
                Optimal RST parameters:
                  Tension = {optimized_params['tension']}
                  Smoothing = {optimized_params['smooth']}
                  RMSE = {optimized_params['rmse']}
            """)
            cv_list = tools.g_list(type="raster", pattern="cv_*", format="json").json

            for cv_map in cv_list:
                aoi_map_figure(
                    tools=tools,
                    map_name=cv_map["name"],
                    relief=LIDAR_DTM_1M_RELIEF
                )
        return optimized_params

    def create_lidar_dem_rst(tools: Tools, points: str, optimization: dict) -> None:
        # Interpolate LiDAR ground points to create DTM using RST
        # Only within the AOI region at 1m resolution
        with gs.RegionManager(region=AOI_REGION, res=AOI_RESOLUTION, flags="a"):

            # tools.r_in_pdal(
            #     input=LIDAR_PATH,
            #     output="lidar_dtm_mean_1m",
            #     method="mean",
            #     resolution=1,
            #     class_filter="2",
            #     flags="we",
            #     quiet=True
            # )

            # tools.r_in_pdal(
            #     input=LIDAR_PATH,
            #     output="lidar_dtm_n_1m",
            #     method="n",
            #     resolution=1,
            #     class_filter="2",
            #     flags="we",
            #     quiet=True
            # )

            # tools.r_in_pdal(
            #     input=LIDAR_PATH,
            #     output="lidar_dsm_max_1m",
            #     method="max",
            #     resolution=1,
            #     return_filter="first",
            #     flags="we",
            #     quiet=True
            # )

            print("Creating LiDAR DTM using RST...")
            smooth = optimization.get("smooth", 0.1)
            tension = optimization.get("tension", 40)
            npmin = optimization.get("npmin", 300)
            flags = optimization.get("flags", "")
            # output = f"{LIDAR_DTM_1M}_rst_n{npmin}_s{smooth}_t{tension}_f{flags}"
            tools.v_surf_rst(
                input=points,
                elevation=LIDAR_DTM_1M,
                slope=f"{LIDAR_DTM_1M}_rst_slope",
                aspect=f"{LIDAR_DTM_1M}_rst_aspect",
                pcurvature=f"{LIDAR_DTM_1M}_rst_pcurv",
                tcurvature=f"{LIDAR_DTM_1M}_rst_tcurv",
                mcurvature=f"{LIDAR_DTM_1M}_rst_mcurv",
                smooth=smooth,
                tension=tension,
                nprocs=30,
                npmin=npmin,
                # mask=LIDAR_DTM_10M,
                flags=flags,
                quiet=True,
            )
            tools.r_relief(
                input=LIDAR_DTM_1M,
                output=LIDAR_DTM_1M_RELIEF,
                quiet=True
            )

    def compute_second_order_derivatives(tools: Tools, input: str) -> list[str]:
        """Compute second order derivatives of the DEM."""
        print("Computing second order derivatives...")
        slope = f"{input}_slope"
        aspect = f"{input}_aspect"
        pcurv = f"{input}_pcurv"
        tcurv = f"{input}_tcurv"
        dx = f"{input}_dx"
        dy = f"{input}_dy"

        tools.r_slope_aspect(
            elevation=input,
            slope=slope,
            aspect=aspect,
            pcurvature=pcurv,
            tcurvature=tcurv,
            dx=dx,
            dy=dy,
            quiet=True
        )

        tools.r_colors(map=slope, color="sepia", flags="e")
        tools.r_colors(map=slope, color="sepia", flags="e")

        # Custom aspect color scheme
        # aspect_color_scheme = """
        # 0       0:60:170      # North
        # 90      0:150:60      # East
        # 180     240:210:60    # South
        # 270     180:40:40     # West
        # 360     0:60:170      # North
        # """

        # Colorblind-safe aspect color scheme
        cb_safe_aspect_color_scheme = """
        0      54:75:154      # deep blue (North)
        45     70:120:194     # blue–cyan
        90     88:166:214     # cyan (East)
        135    120:197:191    # teal
        180    190:215:141    # yellowish (South)
        225    232:196:107    # warm yellow–orange
        270    227:158:167    # pink (West)
        315    170:120:195    # purple
        360    54:75:154      # deep blue (wraps to 0°)
        """
        # tools.r_colors_matplotlib(map=aspect, color="BrBG", flags="e")
        tools.r_colors(
            map=aspect, rules=StringIO(cb_safe_aspect_color_scheme), flags="e"
        )
        return [slope, aspect, pcurv, tcurv]

    def second_order_derivative_island_figures(
            tools: Tools,
            slope: str,
            aspect: str,
            pcurv: str,
            tcurv: str,
            relief: str
    ) -> None:
        """Generate figures for second order derivatives over the full island."""
        # Create full region figures
        full_region_map_figure(
            tools=tools,
            map_name=aspect,
            relief=relief,
            legend_units="\u00b0",  # unicode degree symbol
        )
        full_region_map_figure(
            tools=tools,
            map_name=slope,
            relief=relief,
            legend_units="\u00b0",  # unicode degree symbol
        )
        full_region_map_figure(
            tools=tools, map_name=pcurv, relief=relief, legend_units=""
        )
        full_region_map_figure(
            tools=tools, map_name=tcurv, relief=relief, legend_units=""
        )

    def second_order_derivative_aoi_figures(
        tools: Tools,
        slope: str,
        aspect: str,
        pcurv: str,
        tcurv: str,
        relief: str,
        mcurv: str = None
    ) -> None:
        """Generate figures for second order derivatives over the AOI."""
        # Generate map figures
        aoi_map_figure(
            tools=tools,
            map_name=slope,
            relief=relief,
            legend_units="\u00b0",  # unicode degree symbol
            legend_title="Slope [\u00b0]",
        )

        aoi_map_figure(
            tools=tools,
            map_name=aspect,
            relief=relief,
            legend_units="\u00b0",  # unicode degree symbol
            legend_title="Aspect [\u00b0]",
        )
        aoi_map_figure(
            tools=tools,
            map_name=pcurv,
            relief=relief,
            legend_title="Profile Curvature [m\u207b\u00b9]",
        )
        aoi_map_figure(
            tools=tools,
            map_name=tcurv,
            relief=relief,
            legend_title="Tangential Curvature [m\u207b\u00b9]",
        )

        if mcurv:
            aoi_map_figure(
                tools=tools,
                map_name=mcurv,
                relief=relief,
                legend_title="Mean Curvature [m\\u207b\\u00b9]"
            )

    def flow_accumulation(tools: Tools, input: str, threshold: int) -> None:
        """Compute flow accumulation using multiple methods."""
        print("Computing flow accumulation...")

        # D8 method MFD
        print("D8 MFD method...")
        tools.r_watershed(
            elevation=input,
            accumulation="d8_mfd_flowaccum",
            drainage="d8_mfd_flowdir",
            stream="d8_mfd_streams",
            basin="d8_mfd_basins2",
            threshold=threshold,
            flags="a4",
            quiet=True
        )

        # D8 method SFD
        print("D8 SFD method...")
        tools.r_watershed(
            elevation=input,
            accumulation="d8_sfd_flowaccum",
            drainage="d8_sfd_flowdir",
            threshold=threshold,
            flags="sa",
            quiet=True,
        )

        # D-infinity method SFD
        print("D-infinity SFD method...")
        tools.r_flow(
            elevation=input,
            flowaccumulation="dinf_sfd_flowaccum",
            quiet=True
        )

        # MEFA method
        print("MEFA method...")
        tools.r_flowaccumulation(
            input="d8_sfd_flowdir",
            format="45degree",
            output="MEFA_flowaccum",
            type="CELL",
            quiet=True,
        )

        aoi_map_figure(
            tools=tools,
            map_name="d8_mfd_flowaccum",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="",
            legend_range_min=1,
            legend_flags="lt",
            legend_title="Flow Accumulation [D8 SFD]",
        )

        aoi_map_figure(
            tools=tools,
            map_name="d8_sfd_flowaccum",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="",
            legend_range_min=1,
            legend_flags="lt",
            legend_title="Flow Accumulation [D8 SFD]"
        )

        aoi_map_figure(
            tools=tools,
            map_name="dinf_sfd_flowaccum",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="",
            legend_title="Flow Accumulation [D-infinity SFD]",
            legend_range_min=1,
            legend_flags="btl",
        )

        tools.r_colors(
            map="MEFA_flowaccum",
            rules=Path(PROJECT_DIR, "config/flow_accum_colors.txt"),
            flags="g"
        )

        aoi_map_figure(
            tools=tools,
            map_name="MEFA_flowaccum",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="",
            legend_flags="lt",
            legend_title="Flow Accumulation [MEFA]",
            legend_range_min=1,
            legend_range_max="30000"
        )

    def twi_calculation(tools: Tools, flow_accumulation, slope: str) -> None:
        """Calculate Topographic Wetness Index (TWI)."""
        print("Calculating Topographic Wetness Index (TWI)...")
        tools.r_mapcalc(
            expression=f"twi = log({flow_accumulation} / tan({slope} * 3.14159 / 180))",
            quiet=True,
        )

        twi_color_scheme(tools, "twi")

        # tools.r_colors(map="twi", color="water", flags="en")
        aoi_map_figure(
            tools=tools,
            map_name="twi",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="none",
            legend_flags="ts",
            legend_title="Topographic Wetness Index (TWI)"
        )

    def stream_deliniation(
            tools: Tools,
            elevation: str,
            flow_accumulation: str,
            flow_direction: str,
            threshold: int
    ) -> None:
        """Delineate streams, watersheds, and flow direction."""
        print("Delineating streams and watersheds...")
        # Thin streams
        tools.r_thin(
            input="d8_mfd_streams",
            output="d8_mfd_streams_thin",
            quiet=True
        )

        # Covert streams to vector
        tools.r_to_vect(
            input="d8_mfd_streams_thin",
            output="d8_mfd_streams",
            type="line"
        )

        tools.r_stream_extract(
            elevation=elevation,
            # accumulation=flow_accumulation,
            threshold=threshold,
            direction="stream_extract_dir",
            stream_raster="stream_extract",
            stream_vector="stream_extract",
        )

        # Compute stream order
        print("Computing stream order...")
        tools.r_stream_order(
            elevation=elevation,
            # accumulation=flow_accumulation,
            # direction=flow_direction,
            accumulation=flow_accumulation,
            direction="stream_extract_dir",
            stream_rast="stream_extract",
            # stream_rast="d8_mfd_streams",
            stream_vect="stream_order",
            strahler="strahler",
            horton="horton",
        )

        # Set color tables for stream order maps
        for order_map in ["strahler", "horton"]:
            tools.v_colors(
                map="stream_order", use="attr", column=order_map, color="water"
            )
            tools.r_colors(
                map=order_map, color="water", flags=""
            )

    def hand_method(threshold: int = 50000) -> None:
        print("Calculating Height Above Nearest Drainage (HAND)...")
        tools.r_hand(
            elevation=LIDAR_DTM_1M,
            # streams="d8_mfd_streams",
            # direction="d8_mfd_flowdir",
            threshold=threshold,
            inundation_raster="inundation",
            inundation_strds="inundation_strds",
            start_water_level=0,
            end_water_level=5,
            water_level_step=0.5,
            hand="hand",
            flags="t",
            quiet=True,
        )

        # Apply this fix to r.hand
        hand_colors = """
        0      #f7fbff
        0.5    #deebf7
        1      #c6dbef
        2      #6baed6
        5      #1d91c0
        10     #41ab5d
        20     #78c679
        40     #addd8e
        70%    #fdae61
        100%   #ec7014
        nv     white
        default grey
        """

        tools.r_colors(map="hand", rules=StringIO(hand_colors))

        aoi_map_figure(
            tools=tools,
            map_name="hand",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="m",
            legend_flags="bt",
            shade_flags=""
        )

        class_rules = """
        -30000 thru 0 = NULL
        1 thru 5 = 1 Surface
        5 thru 15 = 2 Shallow
        15 thru 30000 = 3 Deep
        """
        tools.r_reclass(
            input="hand",
            output="hand_class",
            rules=StringIO(class_rules)
        )

        # Set color table for HAND classes
        hand_colors = """
        1 #1d91c0
        2 #41ab5d
        3 #ec7014
        nv white
        default grey
        """
        tools.r_colors(map="hand_class", rules=StringIO(hand_colors))

    def aoi_3d_figure(
        mapcolor: str,
        elevation: str,
        output_name: str,
        legend_units: str = "",
        legend_at="12,17,8,44",
        legend_flags="btd",
        legend_range_min=None,
        legend_range_max=None
    ) -> None:
        print(f"Creating 3D figure: {output_name}...")
        m = gj.Map3D(width=800, height=650, resolution_fine=1)
        m.render(
            elevation_value="0",
            color="#07618B",
            elevation_map=elevation,
            color_map=mapcolor,
            mode=["fine"] * 2,
            resolution_fine=[1, 1],
            resolution_coarse=[9, 9],
            shading=["gouraud"] * 2,
            style=["surface"] * 2,
            wire_color=["136:136:136", "0:0:0"],
            volume="inundation_3d",
            volume_position="0,0,1500",
            height=1200,
            position="0.40,0.05",
            perspective=30,
            twist=0,
            zexag=1.0,
            focus="550,700,0",
            bgcolor="255:255:255",
            light_position="-0.80,0.20,0.75",
            light_brightness=80,
            light_ambient=20,
            light_color="255:255:255",
            fringe=["nw", "se"],
            fringe_color="139:105:20",
            fringe_elevation=43,
            arrow_position=[90, 420],
            arrow_size=200,
            arrow_color="0:0:0",
            flags="nb",
        )

        univar_json = tools.r_univar(map=mapcolor, format="json").json
        _range_min = legend_range_min if legend_range_min is not None else univar_json['min']
        _range_max = legend_range_max if legend_range_max is not None else univar_json['max']
        legend_range = f"{_range_min},{_range_max}"
        m.overlay.d_legend(
            raster=mapcolor,
            at=legend_at,
            font="Fira Sans Condensed Light",
            fontsize=21,
            border_color="none",
            title=f"{legend_units}",
            range=legend_range,
            flags=legend_flags,

        )
        m.overlay.d_barscale(
            at=(60, 12),
            font="Fira Sans Condensed Light",
            fontsize=21,
            length=200,
            flags=""
        )
        m.overlay.d_text(
            text="Oranga Bay",
            at=(53, 40),
            size=3,
            color="white",
            font="Fira Sans Condensed Bold"
        )
        m.save(filename=Path(SAVE_DIR, f"{output_name}_aoi_3d.png"))
        save_jpeg(m.filename, Path(SAVE_DIR, f"{output_name}_aoi_3d.jpg"))

    def volumetric_analysis():
        print("Calculating volumetric analysis...")

        with gs.RegionManager(
            raster="inundation_strds_5.0",
            res=1,
            res3=1,
            t=200,
            b=0,
            flags="ap3"
        ):

            tools.t_rast_to_rast3(
                input="inundation_strds",
                output="inundation_3d"
            )

            tools.r3_info(map="inundation_3d")

            # 3D Flow to outlets
            # dtm_z_3d = f"{LIDAR_DTM_1M}_3d"
            # dtm_dx_3d = f"{LIDAR_DTM_1M}_dx_3d"
            # dtm_dy_3d = f"{LIDAR_DTM_1M}_dy_3d"
            # tools.r_to_rast3(input=LIDAR_DTM_1M, output=dtm_z_3d)
            # tools.r_to_rast3(input=f"{LIDAR_DTM_1M}_dx", output=dtm_dx_3d)
            # tools.r_to_rast3(input=f"{LIDAR_DTM_1M}_dy", output=dtm_dy_3d)
            # tools.r3_flow(
            #     # input="inundation_3d",
            #     vector_field=[dtm_dx_3d, dtm_dy_3d, dtm_z_3d],
            #     flowline="flow3d",
            #     flowaccumulation="flow3d",
            # )

            # Create 3D map figure
            m = gj.Map3D(height=800, width=650, resolution_fine=1)

            # Configure NVIZ image layers (converted from CLI-style invocation)
            m.render(
                elevation_value=0,
                elevation_map=",".join(
                    [
                        f"{LIDAR_DTM_1M}",
                        *[f"inundation_strds_{i}.0" for i in range(1, 6)],
                    ]
                ),
                mode=["fine"] * 7,
                resolution_fine=[1, 1, 1, 1, 1, 1, 1],
                resolution_coarse=[9, 9, 9, 9, 9, 9, 9],
                shading=["gouraud"] * 7,
                style=["surface"] * 7,
                wire_color=[
                    "136:136:136",
                    "136:136:136",
                    "136:136:136",
                    "136:136:136",
                    "136:136:136",
                    "136:136:136",
                    "0:0:0",
                ],
                color_map=LIDAR_DTM_1M,
                surface_position=[
                    [0, 0, 0],
                    [0, 0, 5.5],
                    [0, 0, 5.5],
                    [0, 0, 5.5],
                    [0, 0, 5.5],
                    [0, 0, 5.5],
                    [0, 0, 0],
                ],
                color=[
                    "#F81CBE",  # 1m inundation
                    "#F81C1F",
                    "#F86914",
                    "#F8F01C",
                    "#1C83F8",  # 5m inundation
                    "#07618B",  # Ocean color
                    # "#BFBFBF",  # Constant surface color
                ],
                transparency_value=[0, 0, 0, 0, 0, 0, 0],
                # Contour Options
                vline=f"{LIDAR_DTM_1M}_contours",
                vline_width=[2],
                vline_color=["#FBFBFB"],
                # View options
                position=[0.52, 0.12],
                height=510,
                perspective=5,
                twist=0,
                zexag=1.0,
                focus=[500, 600, 27],
                # Cutting plane options
                cplane=0,
                cplane_rotation=260,
                cplane_tilt=0,
                cplane_position=[500, -20, 0],
                cplane_shading="top",
                # Light options
                light_position=(0.68, -0.68, 0.80),
                light_brightness=80,
                light_ambient=20,
                light_color="255:255:255",
                # Fringe options
                fringe=["nw", "se"],
                fringe_color="#dddad2",
                fringe_elevation=43,
                # Background Color
                bgcolor="#E1F7FF",
            )
            m.save(filename=Path(SAVE_DIR, "inundation_3d.png"))

    def overland_flow(elevation: str) -> None:
        gs.run_command(
            "r.sim.water",
            elevation=elevation,
            dx=f"{elevation}_dx",
            dy=f"{elevation}_dy",
            rain_value=30,  # mm/hr (spatial uniform)
            infil_value=0.0,  # mm/hr
            man_value=0.2,
            niterations=30,  # event duration (minutes)
            output_step=2,  # minutes
            depth="depth",  # m
            discharge="disch",  # m3/s
            random_seed=3,
            nwalkers=100000,
            nprocs=6,  # use all available processors
            flags="t",
        )

    def erosion(elevation: str) -> None:
        print("Calcuating erosion and deposition...")
        tools.r_mapcalc(expression="tranin = 0.001")
        tools.r_mapcalc(expression="detin = 0.001")
        tools.r_mapcalc(expression="shear_stress = 0.5")

        tools.r_sim_sediment(
            elevation=elevation,
            dx=f"{elevation}_dx",
            dy=f"{elevation}_dy",
            water_depth="depth.30",  # meters
            detachment_coeff="detin",  # [s/m]
            transport_coeff="tranin",  # [s]
            shear_stress="shear_stress",  # [Pa]
            man_value=0.04,
            transport_capacity="transport_capacity",
            tlimit_erosion_deposition="tlimit_erosion_deposition",
            sediment_concentration="sediment_concentration",
            sediment_flux="sediment_flux",
            erosion_deposition="erosion_deposition",
            niterations=30,
            output_step=2,
            random_seed=3,
            nprocs=6,
            nwalkers=100000,
        )
        # # Event-based terrain simulation
        # tools.g_extension(extension="r.sim.terrain")
        # tools.r_sim_terrain(
        #     elevation=LIDAR_DTM_1M,
        #     runs="event",
        #     mode="usped_mode",
        #     start="2016-01-01 00:00:00",
        #     rain_interval=1,
        #     temporaltype="absolute",
        #     elevation_timeseries="elevation_timeseries",
        #     depth_timeseries="depth_timeseries",
        #     flux_timeseries="flux_timeseries",
        #     erdep_timeseries="erdep_timeseries",
        #     difference_timeseries="difference_timeseries",
        #     threads=26,
        # )

        def _get_symmetric_range_percentile(map_name: str,
                                            lower: int = 1,
                                            upper: int = 99) -> float:
            """
            Compute a robust symmetric half-range.

            lower, upper: percentile bounds, e.g. 1 and 99.
            """
            stats = tools.r_univar(
                map=map_name,
                flags="e",
                percentile=f"{lower},{upper}",
                format="json"
            ).json
            print(f"Stats for {map_name}: {stats['mean']=}, {stats['min']=}, {stats['max']=}")

            low, high = stats["percentiles"]
            vlow = float(low["value"])
            vhigh = float(high["value"])
            print(f"Using percentiles {lower}: {vlow} and {upper}: {vhigh}.")
            return max(abs(vlow), abs(vhigh))

        def mask_small_values(
                map_name: str,
                out_name: str = None,
                perc: int = 50
        ) -> str:
            if out_name is None:
                out_name = f"{map_name}_masked"

            stats = tools.r_univar(
                map=map_name,
                flags="e",
                percentile=perc,
                format="json"
            ).json
            thr = float(stats["percentiles"][0]["value"])
            expr = f"{out_name} = if(abs({map_name}) < {thr}, null(), {map_name})"
            tools.r_mapcalc(expression=expr)
            return out_name

        def erosion_deposition_color_scheme_robust(
                map_name: str,
                lower: int = 1,
                upper: int = 99
        ) -> None:
            """
            Adaptive, perceptually uniform diverging color scheme for
            erosion/deposition maps using percentile-based robust clipping.
            """
            half_range = _get_symmetric_range_percentile(
                map_name,
                lower,
                upper
            )

            norm_breaks = [
                -1.0, -0.8, -0.5, -0.25, 0.0,
                0.25, 0.5, 0.8, 1.0
            ]

            colors = [
                "#00E5FF",  # -1.0: extreme erosion
                "#2C338B",  # -0.8: very strong erosion
                "#3445A5",  # -0.5: strong erosion
                "#6889FF",  # -0.25: moderate erosion
                "#FFFBD1",  #  0.0: neutral
                "#F7B89C",  # +0.25: slight deposition
                "#E16462",  # +0.5: moderate deposition
                "#B40426",  # +0.8: very strong deposition
                "#D202C8",  # +1.0: extreme deposition
            ]

            color_palette = []
            for nb, col in zip(norm_breaks, colors):
                value = nb * half_range
                color_palette.append((f"{value}", col))

            color_scheme = "\n".join(f"{pos} {color}" for pos, color in color_palette) + "\n"
            tools.r_colors(
                map=map_name,
                rules=StringIO(color_scheme),
                flags="n"
            )

        def thickness_color_scheme_robust(
            map_name: str,
            lower: int = 1,
            upper: int = 99
        ) -> None:
            """
            Adaptive, perceptually uniform diverging color scheme for
            thickness (erosion/deposition) maps using percentile-based robust clipping.
            """
            half_range = _get_symmetric_range_percentile(
                map_name,
                lower,
                upper
            )

            # Slightly tighter inner breakpoints for subtle patterns
            norm_breaks = [-1.0, -0.5, -0.2, 0.0, 0.2, 0.5, 1.0]

            colors = [
                "#3B4CC0",  # deep blue (strong erosion)
                "#6889FF",  # medium blue
                "#AFC9FF",  # light blue
                "#F7F7F7",  # white (neutral)
                "#F7B89C",  # light orange
                "#E16462",  # red-orange
                "#B40426",  # deep red (strong deposition)
            ]

            color_palette = []
            for nb, col in zip(norm_breaks, colors):
                value = nb * half_range
                color_palette.append((f"{value}", col))

            color_scheme = "\n".join(f"{pos} {color}" for pos, color in color_palette) + "\n"
            tools.r_colors(
                map=map_name,
                rules=StringIO(color_scheme),
                flags=""
            )

        def postprocess_erosion(tools: Tools) -> None:
            """Create clipped erosion map and compute thickness in meters and mm."""
            half_range = _get_symmetric_range_percentile("erosion_deposition", lower=2, upper=98)
            tools.r_mapcalc(
                expression=(
                    f"erdep_clip = if(erosion_deposition > {half_range}, {half_range}, "
                    f"if(erosion_deposition < -{half_range}, -{half_range}, "
                    "erosion_deposition))"
                ),
                quiet=True,
            )

            mask_small_values(
                "erdep_clip",
                out_name="erdep_clip_masked",
                perc=60
            )

            tools.r_mapcalc(
                expression="thickness_m = (erdep_clip_masked * 30 * 60) / 1500.0",
                quiet=True,
            )

            tools.r_mapcalc(
                expression="thickness_mm = thickness_m * 1000.0",
                quiet=True,
            )

        postprocess_erosion(tools)
        erosion_deposition_color_scheme_robust("erosion_deposition")
        erosion_deposition_color_scheme_robust("sediment_concentration")
        erosion_deposition_color_scheme_robust("transport_capacity")
        erosion_deposition_color_scheme_robust("erdep_clip")
        erosion_deposition_color_scheme_robust("erdep_clip_masked")
        thickness_color_scheme_robust("thickness_mm")

    def solar_radiation():
        print("Calculating solar radiation...")
        # Winter Solstice
        global_rad_356 = "global_rad_356"
        insol_time_356 = "insol_time_356"
        # refl_rad_356 = "refl_rad_356"
        day_356 = 356

        # Summer Solstice
        global_rad_172 = "global_rad_172"
        insol_time_172 = "insol_time_172"
        # refl_rad_172 = "refl_rad_172"
        day_172 = 172

        # Winter solstice
        tools.r_sun(
            elevation=LIDAR_DTM_1M,
            slope=f"{LIDAR_DTM_1M}_slope",
            aspect=f"{LIDAR_DTM_1M}_aspect",
            glob_rad=global_rad_356,
            insol_time=insol_time_356,
            day=day_356
        )

        # Summer solstice
        tools.r_sun(
            elevation=LIDAR_DTM_1M,
            slope=f"{LIDAR_DTM_1M}_slope",
            aspect=f"{LIDAR_DTM_1M}_aspect",
            glob_rad=global_rad_172,
            insol_time=insol_time_172,
            day=day_172
        )

        color_scheme = """
        0% black
        500 #091f3a
        1000 #1e4271
        1500 #4575b4
        2000 #74add1
        2500 #abd9e9
        3000 #e0f3f8
        4000 #ffffbf
        5000 #fee090
        6000 #fdae61
        8000 #f46d43
        8500 #d73027
        9000 #b30000
        9250 #ae017e
        100% #613a44
        """

        color_scheme = """
        0      #0b0b0b
        500    #0d1f3a
        1000   #1e4271
        1500   #3a78ab
        2000   #5aa5c9
        2500   #86c8dd
        3000   #b5e3f3
        4000   #f3f9d0
        5000   #fff3a0
        6000   #fed675
        7000   #fdb157
        8000   #f9833a
        8500   #e7552e
        9000   #cc301d
        9500   #a81c14
        10000  #7a0b0b
        """
        tools.r_colors(
            map=[global_rad_356, global_rad_172],
            rules=StringIO(color_scheme),
            flags="e"
        )

        aoi_map_figure(
            tools=tools,
            map_name=global_rad_356,
            relief=LIDAR_DTM_1M_SKYVIEW,
            legend_units=" Wh/m\u00b2",  # unicode for squared
            legend_title="Global Solar Radiation [Wh/m\u00b2]",
            legend_flags="t",
        )

        aoi_map_figure(
            tools=tools,
            map_name=global_rad_172,
            relief=LIDAR_DTM_1M_SKYVIEW,
            legend_units=" Wh/m\u00b2",  # unicode for squared
            legend_title="Global Solar Radiation [Wh/m\u00b2]",
            legend_flags="t",
        )

    # Create a new project
    try:
        gs.create_project(path=PROJECT_NAME, epsg="2193")
    except ScriptError:
        print(f"Project {PROJECT_NAME} exists. Using existing project.")

    # Initialize the GRASS session
    with gs.setup.init(PROJECT_NAME) as session:
        # Run GRASS tools
        tools = Tools(session=session, overwrite=True)

        # Install required GRASS add-ons
        # install_grass_addons()

        # Import DSM and DTM at 1m resolution
        # import_dem_data(res=10, tools=tools)

        # Set region and run analysis tools
        tools.g_region(raster=DTM_NAME, flags="a")

        # Set values below 0 to NULL
        set_ocean_to_null(elevation_map=DTM_NAME)
        set_ocean_to_null(elevation_map=DSM_NAME)
        set_ocean_to_null(elevation_map=LIDAR_DTM_10M)

        # Set color tables and compute slope/aspect
        # tools.r_colors(
        #     map=[DTM_NAME, DSM_NAME, LIDAR_DTM_10M],
        #     color="elevation"
        # )
        pounui_island_color_scheme(tools, [DTM_NAME, DSM_NAME, LIDAR_DTM_10M])

        # Resample to 100m, 200m and 300m resolutions
        create_ocean_background()
        resample_dem(tools=tools, input=DTM_NAME, resolutions=[100, 200, 300])

        # Compute relief
        print("Computing relief...")
        # tools.r_relief(input=DTM_NAME, output=DTM_RELIEF, quiet=True)

        # Create 1km grid for reference
        # tools.v_mkgrid(map="grid_1k_1k", box="1000,1000")
        # tools.v_extract(input="grid_1k_1k", cats=27, output=AOI_REGION)

        # print("Computing skyview factor...")
        # tools.r_skyview(input=DTM_NAME, output="lidar_dtm_skyview", ndir=8)
        full_region_map_figure(
            tools=tools,
            map_name=DTM_NAME,
            relief="lidar_dtm_skyview",
            legend_units="m",
            legend_flags="bt"
        )

        # Compute second order derivatives and save results
        slope, aspect, pcurv, tcurv = compute_second_order_derivatives(
            tools=tools,
            input=DTM_NAME
        )

        second_order_derivative_island_figures(
            tools=tools,
            slope=slope,
            aspect=aspect,
            pcurv=pcurv,
            tcurv=tcurv,
            relief=DTM_RELIEF
        )

        # Create save region AOI
        tools.g_region(
            save=AOI_REGION,
            n=5918600.13,
            s=5917599.13,
            w=1793519.48,
            e=1794520.48,
            res=1,
            flags="ap"
        )

        # Compute flow accumulation using multiple methods
        with gs.RegionManager(
            region=AOI_REGION,
            raster=LIDAR_DTM_1M,
            res=1,
            flags="a"
        ):

            # Import LiDAR data and create a 1m DTM
            # process_lidar_data(tools=tools)
            # opt_rst = optimize_rst_params(tools=tools, points="lidar_be")
            opt_rst = {"tension": 500, "smooth": 0.2, "npmin": 300, 'flags': "t"} # Look ok
            opt_rst = {"tension": 800, "smooth": 10, "npmin": 400, 'flags': "t"}  # Currently used
            # create_lidar_dem_rst(
            #     tools=tools,
            #     points="lidar_be",
            #     optimization=opt_rst
            # )
            set_ocean_to_null(elevation_map=LIDAR_DTM_1M)

            # Generate contour lines for the DTM
            tools.r_contour(
                input=LIDAR_DTM_1M,
                output=f"{LIDAR_DTM_1M}_contours",
                step=5
            )
            tools.v_colors(
                map=f"{LIDAR_DTM_1M}_contours", use="attr", column="level", color="grey"
            )
            brown_contour_color_scheme(tools, f"{LIDAR_DTM_1M}_contours")
            create_ocean_background()

            tools.r_relief(
                input=LIDAR_DTM_1M,
                output=LIDAR_DTM_1M_RELIEF,
                quiet=True
            )


            print("Computing skyview factor...")
            tools.r_skyview(input=LIDAR_DTM_1M, output=LIDAR_DTM_1M_SKYVIEW, ndir=8)
            pounui_island_color_scheme(tools, LIDAR_DTM_1M)
            aoi_map_figure(
                tools=tools,
                map_name=LIDAR_DTM_1M,
                relief=LIDAR_DTM_1M_RELIEF,
                legend_title="Elevation [m]",
                legend_units="m",
                legend_flags="st"
            )

            second_order_derivative_aoi_figures(
                tools=tools,
                slope=f"{LIDAR_DTM_1M}_rst_slope",
                aspect=f"{LIDAR_DTM_1M}_rst_aspect",
                pcurv=f"{LIDAR_DTM_1M}_rst_pcurv",
                tcurv=f"{LIDAR_DTM_1M}_rst_tcurv",
                mcurv=f"{LIDAR_DTM_1M}_rst_mcurv",
                relief=LIDAR_DTM_1M_RELIEF,
            )
            pounui_island_color_scheme(tools, "lidar_dtm_mean_1m")
            aoi_map_figure(
                tools=tools,
                map_name="lidar_dtm_mean_1m",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_units="m",
                legend_flags="st"
            )
            pounui_island_color_scheme(tools, "lidar_dsm_max_1m")
            aoi_map_figure(
                tools=tools,
                map_name="lidar_dsm_max_1m",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_units="m",
                legend_flags="st",
            )

            tools.r_colors(
                map="lidar_dtm_n_1m",
                color="viridis",
                flags="e"
            )
            aoi_map_figure(
                tools=tools,
                map_name="lidar_dtm_n_1m",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_title="Bare Earth Points Per Cell",
                legend_units="m",
                legend_flags="st"
            )

            # brown_elev_color_scheme(tools, LIDAR_DTM_1M)

            slope, aspect, pcurv, tcurv = compute_second_order_derivatives(
                tools=tools, input=LIDAR_DTM_1M
            )

            second_order_derivative_aoi_figures(
                tools=tools,
                slope=slope,
                aspect=aspect,
                pcurv=pcurv,
                tcurv=tcurv,
                relief=LIDAR_DTM_1M_RELIEF,
            )

            # 3x3 Median smoothing
            tools.r_neighbors(
                input=LIDAR_DTM_1M,
                output=f"{LIDAR_DTM_1M}_s_med_3x3",
                size=3,
                method="median"
            )

            slope, aspect, pcurv, tcurv = compute_second_order_derivatives(
                tools=tools, input=f"{LIDAR_DTM_1M}_s_med_3x3"
            )

            second_order_derivative_aoi_figures(
                tools=tools,
                slope=slope,
                aspect=aspect,
                pcurv=pcurv,
                tcurv=tcurv,
                relief=LIDAR_DTM_1M_RELIEF,
            )

            # Quadratic edge-preserving smoothing
            lidar_dtm_smooth_qa = f"{LIDAR_DTM_1M}_s_qa"
            smooth_options = {
                "function": "quadratic",
                "input": LIDAR_DTM_1M,
                "output": lidar_dtm_smooth_qa,
                "lambda": 0.4,
                "steps": 20,
            }
            tools.r_smooth_edgepreserve(
                **smooth_options
            )

            slope, aspect, pcurv, tcurv = compute_second_order_derivatives(
                tools=tools, input=lidar_dtm_smooth_qa
            )

            second_order_derivative_aoi_figures(
                tools=tools,
                slope=slope,
                aspect=aspect,
                pcurv=pcurv,
                tcurv=tcurv,
                relief=LIDAR_DTM_1M_RELIEF,
            )

            # Aggressive Tukey's smoothing
            lidar_dtm_smooth_agg_tukey = f"{LIDAR_DTM_1M}_s_agg_tukey"
            smooth_options = {
                "function": "tukey",
                "input": LIDAR_DTM_1M,
                "output": lidar_dtm_smooth_agg_tukey,
                "threshold": 15,
                "lambda": 0.4,
                "steps": 20,
            }
            tools.r_smooth_edgepreserve(**smooth_options)
            pounui_island_color_scheme(tools, lidar_dtm_smooth_agg_tukey)
            aoi_map_figure(
                tools=tools,
                map_name=lidar_dtm_smooth_agg_tukey,
                relief=LIDAR_DTM_1M_RELIEF,
                legend_units="m",
                legend_flags="st",
            )
            slope, aspect, pcurv, tcurv = compute_second_order_derivatives(
                tools=tools, input=lidar_dtm_smooth_agg_tukey
            )

            second_order_derivative_aoi_figures(
                tools=tools,
                slope=slope,
                aspect=aspect,
                pcurv=pcurv,
                tcurv=tcurv,
                relief=LIDAR_DTM_1M_RELIEF,
            )

            # Compute flow accumulation using multiple methods
            flow_accumulation(
                tools=tools,
                input=LIDAR_DTM_1M,
                threshold=100000,
            )

            tools.r_to_vect(
                input="d8_mfd_basins2",
                output="d8_mfd_basins2",
                type="area"
            )
            tools.v_extract(input="d8_mfd_basins2", cats="2", output="basin2")

            # Figure overlay options
            extra_vectors = [
                # {
                #     "map": f"{LIDAR_DTM_1M}_contours",
                #     "type": "line",
                #     # "color": "#FDFDFD",
                #     "width": 1,
                # },
                {
                    "map": "d8_mfd_basins2",
                    "type": "area",
                    "fill_color": "none",
                    "color": "#F5F5F5",
                    "width": 1,
                }
            ]

            extra_shades = [
                {"color": LIDAR_DTM_1M, "shade": LIDAR_DTM_1M_RELIEF, "flags": "n"}
            ]

            # Calculate TWI
            twi_calculation(
                tools=tools,
                flow_accumulation="d8_mfd_flowaccum",
                slope=f"{LIDAR_DTM_1M}_slope"
            )

            # Delineate streams and watersheds
            stream_deliniation(
                tools=tools,
                elevation=LIDAR_DTM_1M,
                flow_accumulation="d8_mfd_flowaccum",
                flow_direction="d8_mfd_flowdir",
                threshold=5000
            )

            # Horton and Strahler stream order

            # Horton Figure
            aoi_map_figure(
                tools=tools,
                map_name=LIDAR_DTM_1M,
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_units="",
                shade_flags="n",
                legend="horton",
                legend_title="Horton Stream Order",
                extra_save_name="horton",
                extra_rasters=[{"map": "horton"}],
                extra_vectors=[
                    *extra_vectors,
                    {
                        "map": "stream_order",
                        "type": "line",
                        "width_column": "horton",
                        "width_scale": 1.5

                    },
                ],
                extra_shades=extra_shades,
            )

            # Strahler Figure
            aoi_map_figure(
                tools=tools,
                map_name=LIDAR_DTM_1M,
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_units="",
                shade_flags="n",
                legend="strahler",
                legend_title="Strahler Stream Order",
                extra_save_name="strahler",
                extra_rasters=[
                    {
                        "map": "strahler"
                    }
                ],
                extra_vectors=[
                    *extra_vectors,
                    {
                        "map": "stream_order",
                        "type": "line",
                        "width_column": "strahler",
                        "width_scale": 1.5
                    },
                ],
                extra_shades=extra_shades,
            )

            # HAND method
            hand_method()
            aoi_map_figure(
                tools=tools,
                map_name="hand_class",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="tc",
                legend_title="Water Table Class",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades
            )

            aoi_map_figure(
                tools=tools,
                map_name="hand",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                shade_flags="n",
                legend_title="Hieght above nearest drainage [m]",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades
            )

            aoi_map_figure(
                tools=tools,
                map_name="inundation_strds_1.0",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_title="Inundation [m]",
                legend_flags="t",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades
            )

            # TPI calculation
            print("Calculating Topographic Position Index (TPI)...")
            tools.r_tpi(
                input=LIDAR_DTM_1M,
                output="tpi"
            )
            tpi_color_scheme = """
            0%     10:76:107
            25%    220:245:255
            50%    255:247:220
            75%    255:230,220
            100%   107:78:76
            """
            tools.r_colors(map="tpi", rules=StringIO(tpi_color_scheme), flags="e")
            aoi_map_figure(
                tools=tools,
                map_name="tpi",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_title="Topographic Position Index (TPI)",
                legend_flags="t",
            )

            # Mask to basin 14 for overland flow and erosion/deposition
            with gs.RegionManager(
                region=AOI_REGION,
                raster=LIDAR_DTM_1M,
                # vector="basin",
                res=1,
                flags="a",
            ):
                with gs.MaskManager():
                    tools.r_mask(vector="d8_mfd_basins2")

                    # Overland flow simulation
                    overland_flow(elevation=LIDAR_DTM_1M)
                    tools.r_mapcalc(expression="max_depth = if(depth.30 >= 0.01, depth.30, null())", quiet=True)
                    tools.r_colors(
                        map="max_depth",
                        raster="depth.30",
                        flags="g"
                    )
                    # Erosion and deposition
                    erosion(elevation=f"{LIDAR_DTM_1M}")

            # Depth figures
            aoi_map_figure(
                tools=tools,
                map_name="depth.30",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="sl",
                shade_flags="n",
                legend_title="Water Depth [m]",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades
            )

            aoi_map_figure(
                tools=tools,
                map_name="max_depth",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="sl",
                legend_title="Water Depth [m]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            # Erosion and deposition figure
            aoi_map_figure(
                tools=tools,
                map_name="erosion_deposition",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_title="Erosion/Deposition [kg/m\u00b2s]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            # erosion_deposition_color_scheme_robust("erosion_deposition")
            aoi_map_figure(
                tools=tools,
                map_name="erosion_deposition",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                shade_flags="n",
                legend_title="Erosion/Deposition [kg/m\u00b2s]",
                extra_save_name="erosion_deposition",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )
            # erosion_deposition_color_scheme_robust("erdep_clip")
            aoi_map_figure(
                tools=tools,
                map_name="erdep_clip",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_title="Erosion/Deposition [kg/m\u00b2s]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            aoi_map_figure(
                tools=tools,
                map_name="erdep_clip_masked",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_title="Erosion/Deposition [kg/m\u00b2s]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )
            # thickness_color_scheme_robust("thickness_mm")
            aoi_map_figure(
                tools=tools,
                map_name="thickness_mm",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="btd",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            aoi_map_figure(
                tools=tools,
                map_name="transport_capacity",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_title="Transport Capacity [kg/m\u00b2s]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            aoi_map_figure(
                tools=tools,
                map_name="tlimit_erosion_deposition",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_title="Transport Limited Erosion/Deposition [kg/m\u00b2s]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            aoi_map_figure(
                tools=tools,
                map_name="sediment_flux",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_title="Sediment Flux [kg/m\u00b2s]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            aoi_map_figure(
                tools=tools,
                map_name="sediment_concentration",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="t",
                legend_title="Sediment Concentration [particle/m\u00b3]",
                shade_flags="n",
                extra_vectors=extra_vectors,
                extra_shades=extra_shades,
            )

            # Solar radiation
            solar_radiation()

            # Volumetric analysis
            volumetric_analysis()

        with gs.RegionManager(
            raster="inundation_strds_5.0",
            res=1,
            res3=5,
            t=100,
            b=0,
            flags="ap3"
        ):
            # 3D figures
            aoi_3d_figure(
                mapcolor=LIDAR_DTM_1M,
                elevation=LIDAR_DTM_1M,
                output_name=LIDAR_DTM_1M,
                legend_units="Elevation [m]"
            )
            aoi_3d_figure(
                mapcolor=f"{LIDAR_DTM_1M}_slope",
                elevation=LIDAR_DTM_1M,
                output_name=f"{LIDAR_DTM_1M}_slope",
                legend_units="Slope [\u00b0]",
            )
            aoi_3d_figure(
                mapcolor=f"{LIDAR_DTM_1M}_aspect",
                elevation=LIDAR_DTM_1M,
                output_name=f"{LIDAR_DTM_1M}_aspect",
                legend_units="Aspect [\u00b0]",
            )

            curvature_color_scheme = """
            -1.10 #225EA8
            -0.7 #1D91C0
            -0.3 #41B6C4
            -0.1 #7FCDAB
            -0.01 #C7E9B4
            0.0 #FFFFFF
            0.01 #FFFFB2
            0.1 #FEDA76
            0.3 #FEB24C
            0.7 #FD8D3C
            1.0 #FC4E2A
            1.35 #83006D
            """

            tools.r_colors(
                map=f"{LIDAR_DTM_1M}_pcurv",
                rules=StringIO(curvature_color_scheme),
                scale="",
                flags="e"
            )
            aoi_3d_figure(
                mapcolor=f"{LIDAR_DTM_1M}_pcurv",
                elevation=LIDAR_DTM_1M,
                output_name=f"{LIDAR_DTM_1M}_pcurv",
                legend_units="Profile Curvature"
            )
            aoi_3d_figure(
                mapcolor=f"{LIDAR_DTM_1M}_tcurv",
                elevation=LIDAR_DTM_1M,
                output_name=f"{LIDAR_DTM_1M}_tcurv",
                legend_units="Tangential Curvature",
            )

            # Tukey smoothed curvature
            aoi_3d_figure(
                mapcolor=lidar_dtm_smooth_agg_tukey + "_pcurv",
                elevation=lidar_dtm_smooth_agg_tukey,
                output_name=lidar_dtm_smooth_agg_tukey + "_pcurv",
                legend_units="Profile Curvature",
            )
            aoi_3d_figure(
                mapcolor=lidar_dtm_smooth_agg_tukey + "_tcurv",
                elevation=LIDAR_DTM_1M,
                output_name=lidar_dtm_smooth_agg_tukey + "_tcurv",
                legend_units="Tangential Curvature",
            )

            aoi_3d_figure(
                mapcolor="max_depth",
                elevation=LIDAR_DTM_1M,
                output_name="max_depth",
                legend_flags="bsld",
                legend_units="Water Depth [m]",
            )
            aoi_3d_figure(
                mapcolor="depth.30",
                elevation="depth.30",
                output_name="max_depth",
                legend_flags="bsld",
                legend_units="Water Depth [m]",
            )
            aoi_3d_figure(
                mapcolor="erdep_clip_masked",
                elevation=LIDAR_DTM_1M,
                output_name="erosion_deposition",
                legend_flags="bsd",
                legend_units="Erosion/Deposition [kg/m\u00b2s]",
            )
            aoi_3d_figure(
                mapcolor="global_rad_172",
                elevation=LIDAR_DTM_1M,
                output_name="global_rad_172",
                legend_units="Global solar radiation [Wh/m\u00b2]",
            )
            aoi_3d_figure(
                mapcolor="global_rad_356",
                elevation=LIDAR_DTM_1M,
                output_name="global_rad_365",
                legend_units="Global solar radiation [Wh/m\u00b2]",
            )
            aoi_3d_figure(
                mapcolor="twi",
                elevation=LIDAR_DTM_1M,
                output_name="twi",
                legend_units="TWI"
            )

            aoi_3d_figure(
                mapcolor="tpi",
                elevation=LIDAR_DTM_1M,
                output_name="tpi_aoi_3d",
                legend_units="TPI",
            )

            aoi_3d_figure(
                mapcolor="d8_mfd_flowaccum",
                elevation=LIDAR_DTM_1M,
                legend_units="Flow Accumulation [D8 MFD]",
                legend_flags="blt",
                legend_range_min=1,
                output_name="d8_mfd_flowaccum_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="d8_sfd_flowaccum",
                elevation=LIDAR_DTM_1M,
                legend_range_min=1,
                legend_units="Flow Accumulation [D8 SFD]",
                legend_at="12,17,8,47",
                legend_flags="blt",
                output_name="d8_sfd_flowaccum_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="dinf_sfd_flowaccum",
                elevation=LIDAR_DTM_1M,
                legend_units="Flow Accumulation [D-infinity SFD]",
                legend_range_min=1,
                legend_at="12,17,8,47",
                legend_flags="btl",
                output_name="dinf_sfd_flowaccum_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="hand_class",
                elevation=LIDAR_DTM_1M,
                legend_units="Water Table Class",
                legend_flags="btc",
                legend_at="12,17,8,47",
                output_name="hand_class_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="hand",
                elevation=LIDAR_DTM_1M,
                legend_units="Hieght above nearest drainage [m]",
                legend_flags="bdt",
                output_name="hand_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="inundation_strds_3.0",
                elevation=LIDAR_DTM_1M,
                legend_units="Inundation [m]",
                legend_flags="bdt",
                output_name="inundation_strds_3.0_aoi_3d",
            )


if __name__ == "__main__":
    main()
