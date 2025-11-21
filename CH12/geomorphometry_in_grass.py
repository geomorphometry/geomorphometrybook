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

# Configuration
PROJECT_NAME = "ponui"
MAPSET_NAME = "PERMANENT"

DSM_PATH = "./data/dsm.cog.tif"
DSM_NAME = "dsm"

DTM_PATH = "data/dtm.cog.tif"
DTM_NAME = "dem"
DTM_RELEIF = "dtm_releif"

LIDAR_PATH = "data/lidar.laz"
LIDAR_DTM_10M = "lidar_dtm_10m"
LIDAR_DTM_NAME = "lidar_dtm"
LIDAR_DTM_RELEIF = "lidar_dtm_releif"

AOI_REGION = "aoi"
SAVE_DIR = "./figures"


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
            releif: str,
            legend_units: str = "none",
            legend_flags: str = "bt"
    ) -> gj.Map:
        univar_json = tools.r_univar(map=map_name, format="json").json
        figure_output = Path(SAVE_DIR, f"{map_name}.png")
        print(f"Saving AOI map figure to {figure_output}")
        m = gj.Map(width=800, use_region=True)
        m.d_shade(color=map_name, shade=releif)

        m.d_legend(
            raster=map_name,
            at="4,38,84,86",
            font="Fira Sans Condensed Light",
            fontsize=12,
            border_color="none",
            units=legend_units,
            range=f"{univar_json['min']},{univar_json['max']}",
            flags=legend_flags,
        )
        m.d_barscale(at=(1, 5), flags="n")
        m.save(filename=figure_output)
        return m

    def aoi_map_figure(
            tools: Tools,
            map_name: str,
            releif: str,
            legend_units: str = "none",
            legend_flags: str = "bt",
            legend_range_max: float | None = None,
    ) -> gj.Map:

        figure_output = Path(SAVE_DIR, f"{map_name}_aoi.png")
        print(f"Saving AOI map figure to {figure_output}")
        m = gj.Map(width=800, saved_region=AOI_REGION)
        m.d_shade(color=map_name, shade=releif)

        univar_json = tools.r_univar(map=map_name, format="json").json
        legend_range = f"{univar_json['min']},{univar_json['max']}"

        if legend_range_max is not None:
            legend_range = f"{univar_json['min']},{legend_range_max}"

        m.d_legend(
            raster=map_name,
            at="4,38,84,86",
            font="Fira Sans Condensed Light",
            fontsize=12,
            border_color="none",
            units=legend_units,
            range=legend_range,
            flags=legend_flags
        )
        m.d_barscale(at=(1, 5), flags="n")
        m.save(filename=figure_output)
        return m

    def install_grass_addons():
        """
        Install required GRASS addons from the gextensions file in parallel.
        """
        print("Installing GRASS addons...")
        try:
            extensions_path = Path("gextensions.txt")
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
        try:
            tools.r_null(
                map=elevation_map,
                setnull="-9999--1",
                quiet=True
            )
        except CalledModuleError as e:
            print(f"Error setting ocean values to NULL: {e}")
            sys.exit(1)

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
            m = gj.Map(
                use_region=False,
                filename=f"{SAVE_DIR}/{resampled_name}.png"
            )
            m.d_rast(map=resampled_name)
            m.d_region_grid(raster=resampled_name, flags="")
            m.show()

    def import_dem_data(tools: Tools, res: float) -> None:
        """Import DSM and DTM data into GRASS at specified resolution."""
        print("Importing DSM and DTM data...")
        try:
            # Import DSM
            tools.r_import(
                input=DSM_PATH,
                output=DSM_NAME,
                resample="bilinear",
                resolution="value",
                resolution_value=res,
                title="Ponui Island 10m DSM",
                quiet=True
            )

            # Import DEM
            tools.r_import(
                input=DTM_PATH,
                output=DTM_NAME,
                resample="bilinear",
                resolution="value",
                resolution_value=res,
                title="Ponui Island 10m DTM",
                quiet=True
            )

            print("Importing LiDAR data and creating mean DTM...")
            # Import LIDAR data and create DTM
            tools.r_in_pdal(
                input=LIDAR_PATH,
                output=LIDAR_DTM_10M,
                method="mean",
                resolution=res,
                return_filter="last",
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
        with gs.RegionManager(region=AOI_REGION, res=1, flags="a"):
            print("Creating LiDAR DTM using RST...")
            tools.v_surf_rst(
                input="lidar_be",
                elevation=LIDAR_DTM_NAME,
                smooth=0.5,
                tension=20,
                quiet=True,
            )
            tools.r_relief(
                input=LIDAR_DTM_NAME,
                output=LIDAR_DTM_RELEIF,
                quiet=True
            )
            tools.r_colors(map=LIDAR_DTM_NAME, color="elevation")
            aoi_map_figure(
                tools=tools,
                map_name=LIDAR_DTM_NAME,
                releif=LIDAR_DTM_RELEIF,
                legend_units="m",
                legend_flags="bst"
            )

    def compute_second_order_derivatives(tools: Tools, input: str) -> None:
        """Compute second order derivatives of the DEM."""
        print("Computing second order derivatives...")
        slope = f"{input}_slope"
        aspect = f"{input}_aspect"
        pcurv = f"{input}_pcurv"
        tcurv = f"{input}_tcurv"
        dx = f"{input}_dx"
        dy = f"{input}_dy"

        layers = [slope, aspect, pcurv, tcurv, dx, dy]

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

        # Generate map figures
        tools.r_colors(map=slope, color="sepia", flags="e")
        aoi_map_figure(
            tools=tools,
            map_name=slope,
            releif="dtm_releif",
            legend_units="degrees"
        )

        tools.r_colors(map=aspect, color="aspectcolr", flags="e")
        aoi_map_figure(
            tools=tools,
            map_name=aspect,
            releif="dtm_releif",
            legend_units="degrees"
        )
        aoi_map_figure(
            tools=tools,
            map_name=pcurv,
            releif="dtm_releif",
            legend_units="none"
        )
        aoi_map_figure(
            tools=tools,
            map_name=tcurv,
            releif="dtm_releif",
            legend_units="none"
        )
        # Create full region figures
        full_region_map_figure(
            tools=tools,
            map_name=aspect,
            releif="dtm_releif",
            legend_units="degrees"
        )
        full_region_map_figure(
            tools=tools,
            map_name=slope,
            releif="dtm_releif",
            legend_units="degrees"
        )
        full_region_map_figure(
            tools=tools,
            map_name=pcurv,
            releif="dtm_releif",
            legend_units="none"
        )
        full_region_map_figure(
            tools=tools,
            map_name=tcurv,
            releif="dtm_releif",
            legend_units="none"
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
            releif=LIDAR_DTM_RELEIF,
            legend_units="cells",
            legend_flags="blt",
        )

        aoi_map_figure(
            tools=tools,
            map_name="d8_sfd_flowaccum",
            releif=LIDAR_DTM_RELEIF,
            legend_units="cells",
            legend_flags="blt",
        )

        aoi_map_figure(
            tools=tools,
            map_name="dinf_sfd_flowaccum",
            releif=LIDAR_DTM_RELEIF,
            legend_units="cells",
            legend_flags="bt",
        )

        tools.r_colors(
            map="MEFA_flowaccum",
            rules="./config/flow_accum_colors.txt",
            flags="g"
        )

        aoi_map_figure(
            tools=tools,
            map_name="MEFA_flowaccum",
            releif=LIDAR_DTM_RELEIF,
            legend_units="cells",
            legend_flags="blt",
            # legend_range_max="30000"
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
        tools.r_relief(input=DTM_NAME, output=DTM_RELEIF, quiet=True)

        print("Computing skyview factor...")
        tools.r_skyview(input=DTM_NAME, output="lidar_dtm_skyview", ndir=8)

        # Compute second order derivatives and save results
        compute_second_order_derivatives(tools=tools, input=DTM_NAME)

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
        set_ocean_to_null(elevation_map=LIDAR_DTM_NAME)
        # Compute flow accumulation using multiple methods
        with gs.RegionManager(region=AOI_REGION, raster=LIDAR_DTM_NAME, res=1, flags="a"):
            flow_accumulation(
                tools=tools,
                input=LIDAR_DTM_NAME,
                threshold=10000
            )


if __name__ == "__main__":
    main()
