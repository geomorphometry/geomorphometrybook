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


def _check_platform():
    platform_id = sys.platform
    print(f"Platform ID: {platform_id}")

    if platform_id == "win32":
        print("This is a Windows system.")
    elif platform_id == "linux":
        print("This is a Linux system.")
    elif platform_id == "darwin":
        print("This is a macOS system.")
    else:
        print(f"Unknown platform ID: {platform_id}")
    return platform_id


def save_jpeg(image: Image.Image, output_path: Path) -> None:
    try:
        # Open the image
        with Image.open(image) as im:
            # Check if the image has an alpha channel and convert to RGB
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB") # Discard the alpha channe
            # Save the image with 300 DPI specified in the metadata
            # For JPEG format
            im.save(output_path, "JPEG", dpi=(300, 300))
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
        m.d_shade(color=map_name, shade=relief)
        # m.d_vect(map="grid_1k_1k", type="boundary", color="grey", width=2)
        m.d_grid(size="00:01:10", color="grey", fontsize=16, flags="ga")
        m.d_vect(map=AOI_REGION, type="boundary", color="black", width=3)

        m.d_legend(
            raster=map_name,
            at="8,30,5,8",
            font="Fira Sans Condensed Light",
            fontsize=24,
            border_color="black",
            units=legend_units,
            range=f"{univar_json['min']},{univar_json['max']}",
            flags=legend_flags,
        )
        m.d_barscale(
            at=(1, 5), font="Fira Sans Condensed Light", fontsize=24, flags="n"
        )

        save_jpeg(m.filename, f"{figure_output}.jpg")
        m.save(filename=f"{figure_output}.png")
        return m

    def aoi_map_figure(
            tools: Tools,
            map_name: str,
            relief: str,
            legend_units: str = "",
            legend_flags: str = "bt",
            legend_range_min: float | None = None,
            legend_range_max: float | None = None,
    ) -> gj.Map:

        figure_output = Path(SAVE_DIR, f"{map_name}_aoi")
        print(f"Saving AOI map figure to {figure_output}")
        m = gj.Map(width=800,
                #    saved_region=AOI_REGION
                    use_region=True   
                )
        m.d_shade(color=map_name, shade=relief)

        univar_json = tools.r_univar(map=map_name, format="json").json
        _range_min = legend_range_min if legend_range_min is not None else univar_json['min']
        _range_max = legend_range_max if legend_range_max is not None else univar_json['max']
        legend_range = f"{_range_min},{_range_max}"

        m.d_legend(
            raster=map_name,
            # at="4,38,84,86",
            at="10,38,4,8",
            font="Fira Sans Condensed Light",
            fontsize=21,
            border_color="none",
            # units=legend_units if legend_units != "" else f" {legend_units}",
            range=legend_range,
            flags=legend_flags,
        )
        m.d_barscale(
            at=(1, 5),
            font="Fira Sans Condensed Light",
            fontsize=21,
            length=250,
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
            output="lidar_be",
            class_filter="2",  # ground points
            flags="o"
        )

        # Interpolate LiDAR ground points to create DTM using RST
        # Only within the AOI region at 1m resolution
        with gs.RegionManager(region=AOI_REGION, res=AOI_RESOLUTION, flags="a"):
            print("Creating LiDAR DTM using RST...")
            tools.v_surf_rst(
                input="lidar_be",
                elevation=LIDAR_DTM_1M,
                smooth=0.5,
                tension=20,
                quiet=True,
            )
            tools.r_relief(
                input=LIDAR_DTM_1M,
                output=LIDAR_DTM_1M_RELIEF,
                quiet=True
            )
            tools.r_colors(map=LIDAR_DTM_1M, color="elevation")


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
        aspect_color_scheme = """
        0       0:60:170      # North
        90      0:150:60      # East
        180     240:210:60    # South
        270     180:40:40     # West
        360     0:60:170      # North
        """
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
            relief: str
    ) -> None:
        """Generate figures for second order derivatives over the AOI."""
        # Generate map figures
        aoi_map_figure(
            tools=tools,
            map_name=slope,
            relief=relief,
            legend_units="\u00b0",  # unicode degree symbol
        )

        aoi_map_figure(
            tools=tools,
            map_name=aspect,
            relief=relief,
            legend_units="\u00b0",  # unicode degree symbol
        )
        aoi_map_figure(
            tools=tools,
            map_name=pcurv,
            relief=relief
        )
        aoi_map_figure(tools=tools, map_name=tcurv, relief=relief)

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
            basin="d8_mfd_basins",
            threshold=threshold,
            flags="a",
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
            legend_flags="blt",
        )

        aoi_map_figure(
            tools=tools,
            map_name="d8_sfd_flowaccum",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="",
            legend_flags="blt",
        )

        aoi_map_figure(
            tools=tools,
            map_name="dinf_sfd_flowaccum",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="",
            legend_flags="bt",
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
            legend_flags="blt",
            # legend_range_max="30000"
        )

    def twi_calculation(tools: Tools, flow_accumulation, slope: str) -> None:
        """Calculate Topographic Wetness Index (TWI)."""
        print("Calculating Topographic Wetness Index (TWI)...")
        tools.r_mapcalc(
            expression=f"twi = log({flow_accumulation} / tan({slope} * 3.14159 / 180))",
            quiet=True,
        )
        tools.r_colors(map="twi", color="byr", flags="en")
        aoi_map_figure(
            tools=tools,
            map_name="twi",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="none",
            legend_flags="bt",
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

        def _stream_map_figure(map_name: str, order_type: str) -> None:
            figure_output = Path(SAVE_DIR, f"{map_name}_{order_type}_aoi.png")

            print(f"Saving AOI map figure to {figure_output}")
            m = gj.Map(width=800, saved_region=AOI_REGION)
            tools.r_mapcalc(expression="ocean = 1")
            color_scheme = """
            1 #0F78BE
            """
            tools.r_colors(map="ocean", rules=StringIO(color_scheme))
            m.d_rast(map="ocean")
            m.d_shade(color="lidar_dtm_slope", shade=LIDAR_DTM_1M_RELIEF)
            m.d_vect(
                map=map_name,
                type="line",
                width_column=order_type,
                attribute_column=order_type,
                label_color="white",
                font="Fira Sans Condensed Bold",
                label_size=16,
            )
            m.d_barscale(at=(1, 5), flags="n")
            m.save(filename=figure_output)

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
            accumulation=flow_accumulation,
            threshold=threshold,
            stream_raster="stream_extract",
            stream_vector="stream_extract",
        )

        # Compute stream order
        print("Computing stream order...")
        tools.r_stream_order(
            elevation=elevation,
            accumulation=flow_accumulation,
            direction=flow_direction,
            stream_rast="d8_mfd_streams",
            stream_vect="stream_order",
            strahler="strahler",
            horton="horton",
        )

        # Set color tables for stream order maps
        for order_map in ["strahler", "horton"]:
            tools.v_colors(
                map="stream_order", use="attr", column=order_map, color="water"
            )
            _stream_map_figure(map_name="stream_order", order_type=order_map)

    def hand_method():
        print("Calculating Height Above Nearest Drainage (HAND)...")
        tools.r_hand(
            elevation=LIDAR_DTM_1M,
            streams="d8_mfd_streams",
            direction="d8_mfd_flowdir",
            inundation_raster="inundation",
            inundation_strds="inundation_strds",
            start_water_level=0,
            end_water_level=5,
            water_level_step=0.5,
            hand="hand",
            flags="t",
            quiet=True,
        )

        aoi_map_figure(
            tools=tools,
            map_name="hand",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="m",
            legend_flags="bt",
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

        hand_colors = """
        1 #1d91c0
        2 #41ab5d
        3 #ec7014
        nv white
        default grey
        """
        tools.r_colors(map="hand_class", rules=StringIO(hand_colors))

        aoi_map_figure(
            tools=tools,
            map_name="hand_class",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="",
            legend_flags="btc",
        )

        aoi_map_figure(
            tools=tools,
            map_name="inundation_strds_5.0",
            relief=LIDAR_DTM_1M_RELIEF,
            legend_units="m",
            legend_flags="bt",
        )

    def aoi_3d_figure(
        mapcolor: str,
        elevation: str,
        output_name: str,
        legend_units: str = "",
        legend_flags="btd",
        legend_range_min=None,
        legend_range_max=None
    ) -> None:
        print(f"Creating 3D figure: {output_name}...")
        m = gj.Map3D(width=800, height=800, resolution_fine=1)
        m.render(
            elevation_map=elevation,
            color_map=mapcolor,
            resolution_fine=1,
            volume="inundation_3d",
            volume_position="0,0,1500",
            isosurf_color_map="inundation_3d",
            isosurf_color_value="100:100:100",
            isosurf_level="1:1,1:2,1:3,1:4,1:5,1:6",
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
            fringe_elevation=0,
            fringe=["nw", "ne", "se", "sw"],
            arrow_position=[90, 480],
            arrow_size=200,
            arrow_color="0:0:0",
            flags="nb"
        )

        univar_json = tools.r_univar(map=mapcolor, format="json").json
        _range_min = legend_range_min if legend_range_min is not None else univar_json['min']
        _range_max = legend_range_max if legend_range_max is not None else univar_json['max']
        legend_range = f"{_range_min},{_range_max}"
        m.overlay.d_legend(
            raster=mapcolor,
            at="12,17,8,44",
            font="Fira Sans Condensed Light",
            fontsize=21,
            border_color="none",
            title=f"{legend_units}",
            range=legend_range,
            flags=legend_flags,

        )
        m.overlay.d_barscale(
            at=(1, 5), font="Fira Sans Condensed Light", fontsize=21, length=250, flags="n"
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

            m = gj.Map3D(width=800, resolution_fine=1)

            # Full list of options m.nviz.image
            # https://grass.osgeo.org/grass84/manuals/m.nviz.image.html
            m.render(
                elevation_map=LIDAR_DTM_1M,
                color_map=f"{LIDAR_DTM_1M}_slope",
                resolution_fine=1,
                volume="inundation_3d",
                arrow_position=[100, 50],
                volume_shading="gouraud",
                volume_resolution=1,
                volume_position="0,0,100",
                isosurf_level="1:100.0,1:150.0,1:200.0,1:250.0,1:300.0,1:350.0",
                # isosurf_level="1:5.0,1:4.0,1:3.0,1:2.0,1:1.0,1:0.0",
                isosurf_color_map="inundation_3d",
                isosurf_color_value="100:100:100",
                # isosurf_transp_value="0,0,0,0,0,0",
                # position="0.84,0.16",
                height=3000,
                perspective=21,
                twist=0,
                zexag=1.0,
                focus="815,334,0",
                bgcolor="255:255:255",
                light_position="0.68,-0.68,0.80",
                light_brightness=80,
                light_ambient=20,
                light_color="255:255:255",
                size="843,739",
            )
            # m.overlay.d_legend(
            #     raster="inundation_3d", at=(60, 97, 87, 92)
            # )
            m.save(filename=Path(SAVE_DIR, "inundation_3d.png"))

    def overland_flow():
        gs.run_command(
            "r.sim.water",
            elevation=LIDAR_DTM_1M,
            dx=f"{LIDAR_DTM_1M}_dx",
            dy=f"{LIDAR_DTM_1M}_dy",
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
            flags="t"
        )

    def erosion():
        print("Calcuating erosion and deposition...")
        tools.r_mapcalc(expression="tranin = 0.001")
        tools.r_mapcalc(expression="detin = 0.001")
        tools.r_mapcalc(expression="shear_stress = 0.01")

        tools.r_sim_sediment(
            elevation=LIDAR_DTM_1M,
            dx=f"{LIDAR_DTM_1M}_dx",
            dy=f"{LIDAR_DTM_1M}_dy",
            water_depth="depth.30",  # meters
            detachment_coeff="detin",  # [s/m]
            transport_coeff="tranin",  # [s]
            shear_stress="shear_stress",  # [Pa]
            man_value=0.2,
            transport_capacity="transport_capacity",
            tlimit_erosion_deposition="tlimit_erosion_deposition",
            sediment_flux="sediment_flux",
            erosion_deposition="erosion_deposition",
            niterations=30,
            output_step=2,
            random_seed=3,
            nprocs=6,  # use all available processors
            nwalkers=100000,
        )

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
            legend_flags="bt",
        )

        aoi_map_figure(
            tools=tools,
            map_name=global_rad_172,
            relief=LIDAR_DTM_1M_SKYVIEW,
            legend_units=" Wh/m\u00b2",  # unicode for squared
            legend_flags="bt",
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
        tools.r_colors(
            map=[DTM_NAME, DSM_NAME, LIDAR_DTM_10M],
            color="elevation"
        )

        # Resample to 100m, 200m and 300m resolutions
        resample_dem(tools=tools, input=DTM_NAME, resolutions=[100, 200, 300])

        # Compute relief
        print("Computing relief...")
        # tools.r_relief(input=DTM_NAME, output=DTM_RELIEF, quiet=True)

        # Create 1km grid for reference
        tools.v_mkgrid(map="grid_1k_1k", box="1000,1000")
        tools.v_extract(input="grid_1k_1k", cats=27, output=AOI_REGION)

        print("Computing skyview factor...")
        tools.r_skyview(input=DTM_NAME, output="lidar_dtm_skyview", ndir=8)
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

        # Import LiDAR data and create a 1m DTM
        # process_lidar_data(tools=tools)
        set_ocean_to_null(elevation_map=LIDAR_DTM_1M)

        # Compute flow accumulation using multiple methods
        with gs.RegionManager(
            region=AOI_REGION,
            raster=LIDAR_DTM_1M,
            res=1,
            flags="a"
        ):
            tools.r_relief(
                input=LIDAR_DTM_1M,
                output=LIDAR_DTM_1M_RELIEF,
                quiet=True
            )
            print("Computing skyview factor...")
            tools.r_skyview(input=LIDAR_DTM_1M, output=LIDAR_DTM_1M_SKYVIEW, ndir=8)
            aoi_map_figure(
                tools=tools,
                map_name=LIDAR_DTM_1M,
                relief=LIDAR_DTM_1M_RELIEF,
                legend_units="m",
                legend_flags="bst"
            )

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

            # Compute flow accumulation using multiple methods
            flow_accumulation(
                tools=tools,
                input=LIDAR_DTM_1M,
                threshold=100000
            )

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
                threshold=50000
            )

            # HAND method
            hand_method()

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
                legend_units="none",
                legend_flags="bt",
            )

            tools.r_to_vect(input="d8_mfd_basins", output="d8_mfd_basins", type="area")
            tools.v_extract(input="d8_mfd_basins", cats="2", output="basin")
            # Mask to basin 14 for overland flow and erosion/deposition
            with gs.RegionManager(vector="basin", res=1, flags="a"):
                with gs.MaskManager():
                    tools.r_mask(vector="basin")

                    # Overland flow simulation
                    # overland_flow()
                    # tools.r_mapcalc(expression="max_depth = if(depth.10 >= 0.005, depth.10, null())", quiet=True)
                    # tools.r_colors(map="max_depth", raster="depth.10", flags="g")
                    # Erosion and deposition
                    # erosion()

            # Depth figure
            aoi_map_figure(
                tools=tools,
                map_name="depth.10",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="bsl",
            )

            aoi_map_figure(
                tools=tools,
                map_name="max_depth",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="bsl",
            )

            # Erosion and deposition figure
            aoi_map_figure(
                tools=tools,
                map_name="erosion_deposition",
                relief=LIDAR_DTM_1M_RELIEF,
                legend_flags="bt",
            )

            # Solar radiation
            # solar_radiation()

            # Volumetric analysis
            # volumetric_analysis()

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

            # curvature_color_scheme = """
            # 0% black
            # -0.1 12,44,132
            # -0.05 34,94,168
            # -0.03 29,145,192
            # -0.02 65,182,196
            # -0.015 127,205,187
            # -0.01 199,233,180
            # 0 white
            # 0.01 255,255,178
            # 0.015 254,217,118
            # 0.02 254,178,76
            # 0.03 253,141,60
            # 0.05 252,78,42
            # 0.1 227,26,28
            # 100% 177,0,38
            # """

            curvature_color_scheme = """
            0% 34,94,168
            10% 29,145,192
            25% 65,182,196
            30% 127,205,187
            45% 199,233,180
            50% white
            55% 255,255,178
            60% 254,217,118
            75% 254,178,76
            90% 253,141,60
            100% 252,78,42
            """

            # tools.r_colors(map=f"{LIDAR_DTM_1M}_pcurv", raster=f"{LIDAR_DTM_1M}_pcurv", scale="0.001", flags="g")
            tools.r_colors(
                map=f"{LIDAR_DTM_1M}_pcurv",
                rules=StringIO(curvature_color_scheme),
                scale="0.001",
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
            aoi_3d_figure(
                mapcolor="max_depth",
                elevation=LIDAR_DTM_1M,
                output_name="max_depth",
                legend_flags="bsld",
                legend_units="Water Depth [m]",
            )
            aoi_3d_figure(
                mapcolor="erosion_deposition",
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
            aoi_3d_figure(mapcolor="twi", elevation=LIDAR_DTM_1M, output_name="twi", legend_units="TWI",)

            # aoi_3d_figure(
            #     mapcolor="global_rad_356",
            #     elevation=LIDAR_DTM_1M,
            #     output_name="global_rad_365",
            #     legend_units="Global solar radiation [Wh/m\u00b2]",
            # )

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
                legend_flags="blt",
                output_name="d8_sfd_flowaccum_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="dinf_sfd_flowaccum",
                elevation=LIDAR_DTM_1M,
                legend_units="Flow Accumulation [D-infinity SFD]",
                legend_range_min=1,
                legend_flags="btl",
                output_name="dinf_sfd_flowaccum_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="hand_class",
                elevation=LIDAR_DTM_1M,
                legend_units="Water Table Class",
                legend_flags="btdc",
                output_name="hand_class_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="hand",
                elevation=LIDAR_DTM_1M,
                legend_units="Hieght above nearest drainage (HAND) [m]",
                legend_flags="bdt",
                output_name="hand_aoi_3d",
            )

            aoi_3d_figure(
                mapcolor="inundation_strds_5.0",
                elevation=LIDAR_DTM_1M,
                legend_units="Inundation [m]",
                legend_flags="bdt",
                output_name="inundation_strds_5.0_aoi_3d",
            )


if __name__ == "__main__":
    main()
