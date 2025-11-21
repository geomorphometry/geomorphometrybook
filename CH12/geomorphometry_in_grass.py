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
LIDAR_PATH = "data/lidar.laz"
LIDAR_DTM_NAME = "lidar_dtm"
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
                output=LIDAR_DTM_NAME,
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
        with gs.RegionManager(region=AOI_REGION, res=1, flags="a"):
            print("Creating LiDAR DTM using RST...")
            tools.v_surf_rst(
                input="lidar_be",
                elevation="lidar_dtm",
                smooth=0.5,
                tension=20,
                quiet=True
            )
            tools.r_relief(input="lidar_dtm", output="lidar_dtm_releif")
            tools.r_colors(map="lidar_dtm", color="elevation")
            # dtm_json = tools.r_univar(map="lidar_dtm", format="json").json
            m = gj.Map(
                width=500,
                saved_region=AOI_REGION,
                filename=Path(SAVE_DIR, "lidar_dtm.png")
            )
            m.d_shade(color="lidar_dtm", shade="lidar_dtm_releif")
            m.d_legend(
                raster="lidar_dtm", at="7,35,2,5", flags="b", unit="m"
            )
            m.d_barscale(at=(1, 5), flags="n")
            m.show()

    def compute_second_order_derivatives(tools: Tools, input: str) -> None:
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

        # Set color tables
        tools.r_colors(map=slope, color="sepia", flags="e")
        tools.r_colors(map=aspect, color="aspectcolr", flags="e")

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
            threshold=threshold,
            flags="sa",
            quiet=True
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
            input="d8_mfd_flowdir",
            output="MEFA_flowaccum",
            quiet=True
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

        # Set color tables and compute slope/aspect
        tools.r_colors(
            map=[DTM_NAME, DSM_NAME, LIDAR_DTM_NAME],
            color="elevation"
        )

        # Resample to 100m, 200m and 300m resolutions
        resample_dem(tools=tools, input=DTM_NAME, resolutions=[100, 200, 300])

        # Compute relief
        print("Computing relief...")
        tools.r_relief(input=DTM_NAME, output="dtm_releif", quiet=True)

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

        # Compute flow accumulation using multiple methods
        flow_accumulation(tools=tools, input=DTM_NAME, threshold=10000)


if __name__ == "__main__":
    main()
