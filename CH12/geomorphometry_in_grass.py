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
# COPYRIGHT: (C) 2025-2026 by Corey T. White, Helena Mitasova, Markus Neteler,
#            Anna Petrasova, Jaroslav Hofierka and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################


from pathlib import Path
from typing import Any, Literal, TYPE_CHECKING
import json
import re
import subprocess
import sys
from io import StringIO
from PIL import Image

if TYPE_CHECKING:
    from grass.tools import Tools

# Configuration
PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_NAME = Path(PROJECT_DIR, "ponui")
MAPSET_NAME = "PERMANENT"

# DSM_PATH = (
#     "https://zenodo.org/records/18314107/files/DEM_ponui_island_dsm.tif"
#     "?download=1"
# )
# Uncomment and adjust the path if you are using a local DSM file
# instead of downloading from Zenodo
DSM_PATH = Path(PROJECT_DIR, "data/dsm.cog.tif")
DSM_NAME = "dsm_10m"

# DTM_PATH = (
#     "https://zenodo.org/records/18314107/files/DEM_ponui_island_dtm.tif"
#     "?download=1"
# )
# Uncomment and adjust the path if you are using a local DTM file
# instead of downloading from Zenodo
DTM_PATH = Path(PROJECT_DIR, "data/dtm.cog.tif")
DTM_NAME = "dem_10m"
DTM_RELIEF = "dtm_relief"

ISLAND_RESOLUTION = 10  # meters

# LIDAR_PATH = (
#     "https://zenodo.org/records/18314107/files/LAS_ponui_island_lidar.zip?download=1"
# )
LIDAR_PATH = Path(PROJECT_DIR, "data/lidar.laz")
LIDAR_DTM_10M = "lidar_dtm_10m"
LIDAR_DTM_1M = "lidar_dtm_1m"
LIDAR_DTM_1M_RELIEF = "lidar_dtm_1m_relief"
LIDAR_DTM_1M_SKYVIEW = "lidar_dtm_1m_skyview"

AOI_REGION = "aoi"
AOI_RESOLUTION = 1  # meters
SAVE_DIR = Path(PROJECT_DIR, "figures")

COLOR_OCEAN = "#0F78BE"


def r_univar_json(tools: "Tools", map_name: str, **kwargs) -> dict:
    """Return `r.univar` JSON output with a fallback for malformed escapes.

    Some environments occasionally produce JSON with invalid unicode escapes
    (e.g., a literal ``\\u`` sequence not followed by 4 hex digits), which
    crashes strict JSON decoders. This helper tries multiple strategies and
    writes the raw output to `figures/` when decoding fails.
    """

    try:
        return tools.r_univar(map=map_name, format="json", **kwargs).json
    except Exception:
        # Fallback to grass.script and manual parsing.
        import grass.script as gs

        raw = gs.read_command(
            "r.univar",
            map=map_name,
            format="json",
            **kwargs,
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Last resort: escape any invalid \u sequences so JSON can parse.
            sanitized = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", raw)
            try:
                return json.loads(sanitized)
            except json.JSONDecodeError as exc:
                try:
                    SAVE_DIR.mkdir(parents=True, exist_ok=True)
                    debug_path = Path(
                        SAVE_DIR,
                        f"bad_json_r_univar_{map_name}.txt",
                    )
                    debug_path.write_text(
                        raw,
                        encoding="utf-8",
                        errors="replace",
                    )
                except Exception:
                    pass
                raise exc


class GeoColors:

    COLOR_SCHEMES = {
        "ocean": [(1, "#0F78BE")],
        "elevation_ponui": [
            ("0%", "#f3e7d3"),
            ("10%", "#d8cfac"),
            ("20%", "#b4c88a"),
            ("35%", "#82b66a"),
            ("50%", "#4f9d53"),
            ("65%", "#2e7a42"),
            ("80%", "#1f5631"),
            ("90%", "#17483b"),
            ("100%", "#0d3a3a"),
        ],
        "solar_radiation": [
            ("0", "#0b0b0b"),
            ("500", "#0d1f3a"),
            ("1000", "#1e4271"),
            ("1500", "#3a78ab"),
            ("2000", "#5aa5c9"),
            ("2500", "#86c8dd"),
            ("3000", "#b5e3f3"),
            ("4000", "#f3f9d0"),
            ("5000", "#fff3a0"),
            ("6000", "#fed675"),
            ("7000", "#fdb157"),
            ("8000", "#f9833a"),
            ("8500", "#e7552e"),
            ("9000", "#cc301d"),
            ("9500", "#a81c14"),
            ("10000", "#7a0b0b"),
        ],
        "aspect_cb_safe": [
            (0, "#364B9A"),
            (45, "#4678C2"),
            (90, "#58A6D6"),
            (135, "#78C5BF"),
            (180, "#BED78D"),
            (225, "#E8C46B"),
            (270, "#E39EA7"),
            (315, "#AA7CC3"),
            (360, "#364B9A"),
        ],
        "tpi": [
            ("0%", "#0A4C6B"),
            ("25%", "#DCF5FF"),
            ("50%", "#FFF7DC"),
            ("75%", "#FFE6DC"),
            ("100%", "#6B4E4C"),
        ],
        "twi": [
            ("0%", "#8c510a"),
            ("20%", "#bf812d"),
            ("40%", "#dfc27d"),
            ("55%", "#f6e8c3"),
            ("70%", "#c7eae5"),
            ("85%", "#5ab4ac"),
            ("100%", "#01665e"),
        ],
        "flow_accum": [
            ("0%", "white"),
            ("10%", "gray"),
            ("20%", "yellow"),
            ("25%", "green"),
            ("30%", "cyan"),
            ("65%", "blue"),
            ("85%", "purple"),
            ("100%", "black")
        ],
        "hand": [
            (0, "#f7fbff"),
            (0.5, "#deebf7"),
            (1, "#c6dbef"),
            (2, "#6baed6"),
            (5, "#1d91c0"),
            (10, "#41ab5d"),
            (20, "#78c679"),
            (40, "#addd8e"),
            (70, "#fdae61"),
            (100, "#ec7014"),
        ],
        "hand_classes": [
            (1, "#1d91c0"),
            (2, "#41ab5d"),
            (3, "#ec7014"),
        ]
    }

    @classmethod
    def list_schemes(cls) -> list[str]:
        """List available color schemes."""
        return list(cls.COLOR_SCHEMES.keys())

    @staticmethod
    def _get_symmetric_range_percentile(
        tools,
        map_name: str,
        lower: int = 1,
        upper: int = 99,
    ) -> float:
        """
        Compute a robust symmetric half-range.

        lower, upper: percentile bounds, e.g. 1 and 99.
        """
        stats = r_univar_json(
            tools,
            map_name,
            flags="e",
            percentile=f"{lower},{upper}",
        )
        low, high = stats["percentiles"]
        vlow = float(low["value"])
        vhigh = float(high["value"])
        return max(abs(vlow), abs(vhigh))

    @classmethod
    def adaptive_color_schemes(
        cls,
        tools,
        map_name: str,
        palette_name: str,
        lower: int = 1,
        upper: int = 99,
        **kwargs
    ) -> None:
        """
        Adaptive, perceptually uniform diverging color scheme for
        erosion/deposition maps using percentile-based robust clipping.
        """
        half_range = cls._get_symmetric_range_percentile(
            tools,
            map_name,
            lower,
            upper
        )

        palette = cls.COLOR_SCHEMES.get(palette_name)
        if palette is None:
            print(f"Color scheme '{palette_name}' not found.")
            return
        palette_colors = palette.get("colors", [])
        palette_breaks = palette.get("norm_breaks", [])
        zipped_breaks = zip(palette_breaks, palette_colors)
        color_palette = [
            (f"{nb * half_range}", col) for nb, col in zipped_breaks
        ]

        color_scheme = cls._create_color_scheme(color_palette)
        tools.r_colors(
            **kwargs,
            map=map_name,
            rules=color_scheme
        )

    @staticmethod
    def _create_color_scheme(rules: list[tuple]) -> StringIO:
        """
        Create a color scheme for r_colors or v_colors from a list of rules.

        :param rules: List of tuples containing position and color
        :type rules: list[tuple]
        :return: Color scheme as StringIO
        :rtype: StringIO
        """
        scheme = "\n".join(f"{pos} {color}" for pos, color in rules) + "\n"
        return StringIO(scheme)

    @classmethod
    def colors(
        cls,
        maps: str | list[str],
        scheme_name: str,
        tools: object,
        **kwargs
    ) -> None:
        """Apply color scheme to a list of maps."""
        if scheme_name not in cls.COLOR_SCHEMES:
            print(f"Color scheme '{scheme_name}' not found.")
            return

        rules = cls.COLOR_SCHEMES[scheme_name]
        color_scheme = cls._create_color_scheme(rules)

        tools.r_colors(**kwargs, map=maps, rules=color_scheme)


def save_jpeg(image_path: str | Path, output_path: str | Path) -> None:
    try:
        # Open the image
        with Image.open(image_path) as im:
            # Check if the image has an alpha channel and convert to RGB
            if im.mode in ("RGBA", "P"):
                # im = im.convert("RGB", dither=None)
                # White matches the background of map grid
                background = Image.new("RGB", im.size, color=(255, 255, 255))
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
                im.convert("RGB").save(
                    output_path,
                    "JPEG",
                    dpi=(300, 300),
                    quality=100
                )

            print(f"Image successfully saved to {output_path} with 300 DPI.")

    except FileNotFoundError:
        print(f"Error: The file '{image_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def _add_grass_to_syspath() -> None:
    """Add GRASS Python modules to `sys.path`.

    Uses `grass --config python_path`.
    Imports of `grass.*` stay localized to runtime so the script can be
    imported or syntax-checked without GRASS.
    """

    try:
        grass_python_path = subprocess.check_output(
            ["grass", "--config", "python_path"],
            text=True,
        ).strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            "GRASS executable 'grass' not found on PATH. "
            "Install GRASS or ensure 'grass' is available."
        ) from exc

    if grass_python_path and grass_python_path not in sys.path:
        sys.path.append(grass_python_path)


def _ensure_save_dir() -> None:
    """Ensure the figures output directory exists."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def _legend_range(
    univar_json: dict,
    legend_range_min: float | None,
    legend_range_max: float | None,
) -> str:
    range_min = legend_range_min
    if range_min is None:
        range_min = univar_json["min"]

    range_max = legend_range_max
    if range_max is None:
        range_max = univar_json["max"]

    return f"{range_min},{range_max}"


def _apply_scaled_color_rules(
    tools: Any,
    map_name: str,
    *,
    half_range: float,
    norm_breaks: list[float],
    colors: list[str],
    flags: str,
) -> None:
    rules = [(f"{nb * half_range}", col)
             for nb, col in zip(norm_breaks, colors)]
    tools.r_colors(
        map=map_name,
        rules=GeoColors._create_color_scheme(rules),
        flags=flags,
    )


def erosion_deposition_color_scheme_robust(
    tools: Any,
    map_name: str,
    lower: int = 1,
    upper: int = 99,
) -> None:
    half_range = GeoColors._get_symmetric_range_percentile(
        tools,
        map_name,
        lower=lower,
        upper=upper,
    )

    norm_breaks = [-1.0, -0.8, -0.5, -0.25, 0.0, 0.25, 0.5, 0.8, 1.0]
    colors = [
        "#00E5FF",  # extreme erosion
        "#2C338B",  # very strong erosion
        "#3445A5",  # strong erosion
        "#6889FF",  # moderate erosion
        "#FFFBD1",  # neutral
        "#F7B89C",  # slight deposition
        "#E16462",  # moderate deposition
        "#B40426",  # very strong deposition
        "#D202C8",  # extreme deposition
    ]
    _apply_scaled_color_rules(
        tools,
        map_name,
        half_range=half_range,
        norm_breaks=norm_breaks,
        colors=colors,
        flags="n",
    )


def full_region_map_figure(
    tools: Any,
    map_name: str,
    relief: str,
    legend_units: str = "",
    legend_flags: str = "bt",
) -> Any:
    """Render a full-region shaded raster figure and save it as PNG/JPG."""
    import grass.jupyter as gj

    univar_json = r_univar_json(tools, map_name)
    figure_output = Path(SAVE_DIR, f"{map_name}")
    print(f"Saving full-region figure to {figure_output}")

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
    highlight = ("#1F78B4", "#7B3294", "#E66101")
    m.d_vect(map=AOI_REGION, type="boundary", color=highlight[2], width=3)
    m.d_text(
        text="Oranga Bay",
        at=(34, 53),
        size=2.25,
        color="#FDFDFD",
        font="Fira Sans Condensed Bold",
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

    save_jpeg(m.filename, Path(f"{figure_output}.jpg"))
    m.save(filename=f"{figure_output}.png")
    return m


def aoi_map_figure(
    tools: Any,
    map_name: str,
    relief: str,
    legend: str | None = None,
    legend_units: str = "",
    legend_title: str = "",
    legend_flags: str = "t",
    legend_at: str | None = None,
    legend_range_min: float | None = None,
    legend_range_max: float | None = None,
    legend_orientation: Literal["horizontal", "vertical"] = "horizontal",
    shade_flags: str = "n",
    extra_save_name: str | None = None,
    extra_rasters: list[dict] | None = None,
    extra_vectors: list[dict] | None = None,
    extra_shades: list[dict] | None = None,
) -> Any:
    """Render an AOI map figure (with optional overlays) and save PNG/JPG.

    `legend_orientation` controls the layout used for the legend, text label,
    and scale bar. ``"horizontal"`` is the default; ``"vertical"`` shifts the
    region eastward to make room for a vertical legend strip.
    """
    import grass.script as gs
    import grass.jupyter as gj

    if legend_orientation == "vertical":
        region_shift = {"e": "e+350"}
        default_legend_at = "35,90,78,84"
        grid_border_color = None
        text_at = (20, 80)
        barscale_at = (40, 6)
    else:
        region_shift = {"s": "s-200"}
        default_legend_at = "5,10,20,80"
        grid_border_color = "#FFFFFF"
        text_at = (20, 84)
        barscale_at = (60, 22)

    if legend_at is None:
        legend_at = default_legend_at

    save_name = (
        f"{extra_save_name}_aoi" if extra_save_name else f"{map_name}_aoi"
    )
    figure_output = Path(SAVE_DIR, save_name)
    univar_json = r_univar_json(tools, map_name)
    legend_range = _legend_range(
        univar_json,
        legend_range_min,
        legend_range_max,
    )
    print(f"Saving AOI map figure to {figure_output}")

    with gs.RegionManager(
        region=AOI_REGION,
        raster=LIDAR_DTM_1M,
        res=AOI_RESOLUTION,
        flags="a",
        **region_shift,
    ):
        m = gj.Map(width=800, use_region=True)
        m.d_rast(map="ocean")

        if extra_shades:
            for shade in extra_shades:
                m.d_shade(**shade)

        m.d_shade(color=map_name, shade=relief, flags=shade_flags)

        if extra_rasters:
            for rast in extra_rasters:
                m.d_rast(**rast)

        if extra_vectors:
            for vec in extra_vectors:
                m.d_vect(**vec)

        grid_kwargs = dict(
            size="00:00:10",
            color="#FDFDFD",
            text_color="#FDFDFD",
            fontsize=16,
            flags="gac",
        )
        if grid_border_color is not None:
            grid_kwargs["border_color"] = grid_border_color
        m.d_grid(**grid_kwargs)
        m.d_text(
            text="Oranga Bay",
            at=text_at,
            size=4,
            color="white",
            font="Fira Sans Condensed Bold",
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
            units=legend_units,
            range=legend_range,
            flags=legend_flags,
        )
        m.d_barscale(
            at=barscale_at,
            font="Fira Sans Condensed Light",
            fontsize=21,
            length=250,
            bgcolor="none",
            style="line",
            color="#FDFDFD",
            flags="n",
        )

        save_jpeg(m.filename, Path(f"{figure_output}.jpg"))
        m.save(filename=f"{figure_output}.png")
        return m


def install_grass_addons(extensions_path: Path | None = None) -> None:
    """Install required GRASS addons listed in `gextensions.txt`."""
    from grass.exceptions import CalledModuleError
    from grass.tools import Tools
    import grass.script.core as gcore

    print("Installing GRASS addons:")
    extensions_path = extensions_path or Path(PROJECT_DIR, "gextensions.txt")

    try:
        with extensions_path.open() as f:
            exts = [
                line.strip()
                for line in f
                if line.strip() and not line.lstrip().startswith("#")
            ]
    except FileNotFoundError:
        print("gextensions file not found.")
        sys.exit(1)

    if not exts:
        print("No extensions listed in gextensions.txt.")
        return

    with Tools() as tools:
        failed: list[str] = []
        for ext in exts:
            if not gcore.find_program(ext, "--help"):
                print(f"\tInstalling {ext}...")
                try:
                    tools.g_extension(extension=ext, quiet=True)
                except CalledModuleError as e:
                    print(f"Error installing {ext}: {e}")
                    failed.append(ext)
            else:
                print(f"\t{ext} already installed skipping.")

        if failed:
            print(f"Failed to install extensions: {', '.join(failed)}")
            sys.exit(1)


def set_ocean_to_null(tools: Any, elevation_map: str) -> None:
    """Set ocean values (below 0) to NULL in the elevation map."""
    tools.r_null(map=elevation_map, setnull="-9999-0", quiet=True)


def create_ocean_background(tools: Any) -> None:
    """Create an ocean background raster and random-surface layers."""
    tools.r_mapcalc(expression="ocean = 1")
    ocean_color_scheme = GeoColors._create_color_scheme([(1, COLOR_OCEAN)])
    tools.r_colors(map="ocean", rules=ocean_color_scheme)


def ponui_island_color_scheme(tools: Any, map_name: str | list[str]) -> None:
    """Apply the Ponui Island elevation palette to one or more rasters."""
    GeoColors.colors(
        maps=map_name,
        scheme_name="elevation_ponui",
        tools=tools
    )


def twi_color_scheme(tools: Any, map_name: str) -> None:
    """Apply the TWI blue-green color scheme."""
    GeoColors.colors(map_name, "twi", tools, flags="e")


def resample_dem(tools: Any, dem: str, resolutions: list[float]) -> None:
    """Resample a raster DEM to multiple resolutions.

    Saves preview figures for each resolution.
    """
    import grass.script as gs
    import grass.jupyter as gj
    from grass.exceptions import CalledModuleError

    for res in resolutions:
        with gs.RegionManager(res=res, raster=dem, flags=""):
            resampled_name = f"{dem}_{int(res)}m"
            try:
                tools.r_resamp_interp(
                    input=dem,
                    output=resampled_name,
                    method="bilinear",
                    quiet=True,
                )
            except CalledModuleError as e:
                print(f"Error resampling to {res}m: {e}")
                sys.exit(1)

        m = gj.Map(use_region=False)
        m.d_rast(map="ocean")
        m.d_rast(map=resampled_name)
        m.d_region_grid(
            raster=resampled_name,
            flags="",
            width=1,
            color="#FDFDFD",
        )
        save_jpeg(m.filename, Path(SAVE_DIR, f"{resampled_name}.jpg"))
        m.save(filename=str(Path(SAVE_DIR, f"{resampled_name}.png")))


def import_dem_data(tools: Any, res: float) -> None:
    """Import DSM/DTM rasters and derive a mean LiDAR DTM raster."""
    print(f"Importing DSM and DTM data at {res}m...")
    try:
        tools.r_import(
            input=DSM_PATH,
            output=DSM_NAME,
            resample="bilinear",
            resolution="value",
            resolution_value=res,
            title=f"Ponui Island {res}m DSM",
            quiet=True,
        )
        tools.r_import(
            input=DTM_PATH,
            output=DTM_NAME,
            resample="bilinear",
            resolution="value",
            resolution_value=res,
            title=f"Ponui Island {res}m DTM",
            quiet=True,
        )

        print("Importing LiDAR data and creating mean DTM...")
        tools.r_in_pdal(
            input=LIDAR_PATH,
            output=LIDAR_DTM_10M,
            method="mean",
            resolution=res,
            class_filter="2",
            flags="we",
            quiet=True,
        )
    except Exception as e:
        print(f"Error importing data: {e}")
        sys.exit(1)


def process_lidar_data(tools: Any) -> None:
    """Import LiDAR ground points as a vector."""
    print("Importing LiDAR data...")
    tools.v_in_pdal(
        input=LIDAR_PATH,
        output="lidar_be",
        class_filter="2",  # ground points
        flags="or",
    )


def create_lidar_dem_rst(tools: Any, points: str, optimization: dict) -> None:
    """Interpolate LiDAR ground points to create a 1m DTM using RST."""
    import grass.script as gs

    with gs.RegionManager(region=AOI_REGION, res=AOI_RESOLUTION, flags="a"):
        tools.r_in_pdal(
            input=LIDAR_PATH,
            output="lidar_dtm_n_1m",
            method="n",
            resolution=1,
            class_filter="2",
            flags="we",
            quiet=True,
        )

        print("Creating LiDAR DTM using RST...")
        smooth = optimization.get("smooth", 0.1)
        tension = optimization.get("tension", 40)
        npmin = optimization.get("npmin", 300)
        dmin = optimization.get("dmin", 0.5)
        flags = optimization.get("flags", "")

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
            dmin=dmin,
            flags=flags,
            quiet=True,
        )
        tools.r_relief(
            input=LIDAR_DTM_1M,
            output=LIDAR_DTM_1M_RELIEF,
            quiet=True,
        )


def compute_second_order_derivatives(
    tools: Any,
    dem: str,
) -> tuple[str, str, str, str]:
    """Compute slope, aspect, and curvature rasters for a DEM."""
    print("Computing second order derivatives...")
    slope = f"{dem}_slope"
    aspect = f"{dem}_aspect"
    pcurv = f"{dem}_pcurv"
    tcurv = f"{dem}_tcurv"
    dx = f"{dem}_dx"
    dy = f"{dem}_dy"

    tools.r_slope_aspect(
        elevation=dem,
        slope=slope,
        aspect=aspect,
        pcurvature=pcurv,
        tcurvature=tcurv,
        dx=dx,
        dy=dy,
        quiet=True,
    )

    tools.r_colors(map=slope, color="sepia", flags="e")
    GeoColors.colors(aspect, "aspect_cb_safe", tools, flags="e")
    return slope, aspect, pcurv, tcurv


def second_order_derivative_island_figures(
    tools: Any,
    slope: str,
    aspect: str,
    pcurv: str,
    tcurv: str,
    relief: str,
) -> None:
    """Generate full-island figures for slope/aspect/curvature products."""
    full_region_map_figure(
        tools=tools,
        map_name=aspect,
        relief=relief,
        legend_units="°",
    )
    full_region_map_figure(
        tools=tools,
        map_name=slope,
        relief=relief,
        legend_units="°",
    )
    full_region_map_figure(
        tools=tools,
        map_name=pcurv,
        relief=relief,
        legend_units="",
    )
    full_region_map_figure(
        tools=tools,
        map_name=tcurv,
        relief=relief,
        legend_units="",
    )


def second_order_derivative_aoi_figures(
    tools: Any,
    slope: str,
    aspect: str,
    pcurv: str,
    tcurv: str,
    relief: str,
    mcurv: str | None = None,
) -> None:
    """Generate AOI figures for slope/aspect/curvature products."""
    aoi_map_figure(
        tools=tools,
        map_name=slope,
        relief=relief,
        legend_units="°",
        legend_title="Slope [°]",
    )
    aoi_map_figure(
        tools=tools,
        map_name=aspect,
        relief=relief,
        legend_units="°",
        legend_title="Aspect [°]",
    )
    aoi_map_figure(
        tools=tools,
        map_name=pcurv,
        relief=relief,
        legend_title="Profile Curvature [m⁻¹]",
    )
    aoi_map_figure(
        tools=tools,
        map_name=tcurv,
        relief=relief,
        legend_title="Tangential Curvature [m⁻¹]",
    )

    if mcurv:
        aoi_map_figure(
            tools=tools,
            map_name=mcurv,
            relief=relief,
            legend_title="Mean Curvature [m⁻¹]",
        )


def flow_accumulation(tools: Any, dem: str, threshold: int) -> None:
    """Compute flow accumulation using multiple GRASS methods.

    Also saves AOI figures.
    """
    print("Computing flow accumulation...")

    print("D8 MFD method...")
    tools.r_watershed(
        elevation=dem,
        accumulation="d8_mfd_flowaccum",
        drainage="d8_mfd_flowdir",
        stream="d8_mfd_streams",
        basin="d8_mfd_basins2",
        threshold=threshold,
        flags="a",
        quiet=True,
    )

    print("D8 SFD method...")
    tools.r_watershed(
        elevation=dem,
        accumulation="d8_sfd_flowaccum",
        drainage="d8_sfd_flowdir",
        threshold=threshold,
        flags="sa",
        quiet=True,
    )

    print("D-infinity SFD method...")
    tools.r_flow(
        elevation=dem,
        flowaccumulation="dinf_sfd_flowaccum",
        quiet=True,
    )
    set_ocean_to_null(tools, "dinf_sfd_flowaccum")

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
        legend_title="Flow Accumulation [D8 MFD]",
    )
    aoi_map_figure(
        tools=tools,
        map_name="d8_sfd_flowaccum",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_units="",
        legend_range_min=1,
        legend_flags="lt",
        legend_title="Flow Accumulation [D8 SFD]",
    )
    aoi_map_figure(
        tools=tools,
        map_name="dinf_sfd_flowaccum",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_units="",
        shade_flags="n",
        legend_title="Flow Accumulation [D-infinity SFD]",
        legend_range_min=1,
        legend_flags="tl",
    )

    GeoColors.colors("MEFA_flowaccum", "flow_accum", tools, flags="g")
    aoi_map_figure(
        tools=tools,
        map_name="MEFA_flowaccum",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_units="",
        legend_flags="lt",
        legend_title="Flow Accumulation [MEFA]",
        legend_range_min=1,
        legend_range_max="70000",
    )


def twi_calculation(tools: Any, flow_accumulation: str, slope: str) -> None:
    """Calculate Topographic Wetness Index (TWI) and save an AOI figure."""
    print("Calculating Topographic Wetness Index (TWI)...")

    # Note: log is the natural log, not base 10.
    # The slope is in degrees and is getting converted to radians
    expression = (
        f"twi = log({flow_accumulation} / tan({slope} * 3.14159 / 180))"
    )
    tools.r_mapcalc(expression=expression, quiet=True)

    twi_color_scheme(tools, "twi")
    aoi_map_figure(
        tools=tools,
        map_name="twi",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_units="none",
        legend_flags="ts",
        legend_title="Topographic Wetness Index (TWI)",
    )


def stream_delineation(
    tools: Any,
    elevation: str,
    flow_accumulation: str,
    flow_direction: str,
    threshold: int,
) -> None:
    """Delineate streams and compute stream order products.

    Note: `flow_direction` is currently unused (kept for API compatibility and
    future experiments).
    """
    print("Delineating streams and watersheds...")
    tools.r_thin(
        input="d8_mfd_streams",
        output="d8_mfd_streams_thin",
        quiet=True,
    )

    tools.r_to_vect(
        input="d8_mfd_streams_thin",
        output="d8_mfd_streams",
        type="line",
    )

    tools.r_stream_extract(
        elevation=elevation,
        threshold=threshold,
        direction="stream_extract_dir",
        stream_raster="stream_extract",
        stream_vector="stream_extract",
    )

    print("Computing stream order...")
    tools.r_stream_order(
        elevation=elevation,
        accumulation=flow_accumulation,
        direction="stream_extract_dir",
        stream_rast="stream_extract",
        stream_vect="stream_orders",
        strahler="strahler",
        horton="horton",
    )

    for order_map in ["strahler", "horton"]:
        tools.v_colors(
            map="stream_orders",
            use="attr",
            column=order_map,
            color="water",
        )
        tools.r_colors(map=order_map, color="water", flags="")


def hand_method(
    tools: Any,
    threshold: int = 50000,
    extra_vectors: list[dict] | None = None,
    extra_shades: list[dict] | None = None,
) -> None:
    """Run the HAND workflow and generate the HAND rasters."""
    print("Calculating Height Above Nearest Drainage (HAND)...")
    tools.r_hand(
        elevation=LIDAR_DTM_1M,
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

    GeoColors.colors(maps="hand", scheme_name="hand", tools=tools)

    aoi_map_figure(
        tools=tools,
        map_name="hand",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_flags="t",
        shade_flags="n",
        legend_title="Height above nearest drainage [m]",
        extra_vectors=extra_vectors,
        extra_shades=extra_shades,
    )

    class_rules = """
    -30000 thru 0 = NULL
    0 thru 5 = 1 Surface
    5 thru 15 = 2 Shallow
    15 thru 30000 = 3 Deep
    """
    tools.r_reclass(
        input="hand",
        output="hand_class",
        rules=StringIO(class_rules),
    )

    GeoColors.colors(
        maps="hand_class",
        scheme_name="hand_classes",
        tools=tools
    )

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
        map_name="inundation_strds_1.0",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_title="Inundation [m]",
        legend_flags="t",
        shade_flags="n",
        extra_vectors=extra_vectors,
        extra_shades=extra_shades
    )


def aoi_3d_figure(
    tools: Any,
    mapcolor: str,
    elevation: str,
    output_name: str,
    legend_units: str = "",
    legend_at: str = "12,17,8,44",
    legend_flags: str = "btd",
    legend_range_min: float | None = None,
    legend_range_max: float | None = None,
) -> None:
    """Create and save a 3D figure over the AOI using `grass.jupyter.Map3D`."""
    import grass.jupyter as gj

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

    univar_json = r_univar_json(tools, mapcolor)
    legend_range = _legend_range(
        univar_json,
        legend_range_min,
        legend_range_max,
    )

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
        flags="",
    )
    m.overlay.d_text(
        text="Oranga Bay",
        at=(53, 40),
        size=3,
        color="white",
        font="Fira Sans Condensed Bold",
    )

    m.save(filename=Path(SAVE_DIR, f"{output_name}_aoi_3d.png"))


def overland_flow(tools: Any, elevation: str) -> None:
    """Simulate overland flow and derive a `max_depth` raster."""
    import grass.script as gs

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
        nprocs=6,
        flags="t",
    )

    tools.r_mapcalc(
        expression="max_depth = if(depth.30 >= 0.01, depth.30, null())",
        quiet=True,
    )
    tools.r_colors(map="max_depth", raster="depth.30", flags="g")


def erosion(tools: Any, elevation: str) -> None:
    """Run erosion/deposition simulation and post-process derived rasters."""
    print("Calculating erosion and deposition...")
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
        nprocs=26,
        nwalkers=100000,
    )

    erosion_deposition_color_scheme_robust(tools, "erosion_deposition")
    erosion_deposition_color_scheme_robust(tools, "sediment_concentration")
    erosion_deposition_color_scheme_robust(tools, "transport_capacity")


def solar_radiation(tools: Any) -> None:
    """Compute winter/summer solstice solar radiation rasters and figures."""
    print("Calculating solar radiation...")

    global_rad_356 = "global_rad_356"
    insol_time_356 = "insol_time_356"
    day_356 = 356

    global_rad_172 = "global_rad_172"
    insol_time_172 = "insol_time_172"
    day_172 = 172

    tools.r_sun(
        elevation=LIDAR_DTM_1M,
        slope=f"{LIDAR_DTM_1M}_slope",
        aspect=f"{LIDAR_DTM_1M}_aspect",
        glob_rad=global_rad_356,
        insol_time=insol_time_356,
        day=day_356,
    )

    tools.r_sun(
        elevation=LIDAR_DTM_1M,
        slope=f"{LIDAR_DTM_1M}_slope",
        aspect=f"{LIDAR_DTM_1M}_aspect",
        glob_rad=global_rad_172,
        insol_time=insol_time_172,
        day=day_172,
    )

    GeoColors.colors(
        maps=[global_rad_356, global_rad_172],
        scheme_name="solar_radiation",
        tools=tools,
        flags="e",
    )

    aoi_map_figure(
        tools=tools,
        map_name=global_rad_356,
        relief=LIDAR_DTM_1M_SKYVIEW,
        legend_units=" Wh/m\u00b2",
        legend_title="Global Solar Radiation [Wh/m\u00b2]",
        legend_flags="t",
    )
    aoi_map_figure(
        tools=tools,
        map_name=global_rad_172,
        relief=LIDAR_DTM_1M_SKYVIEW,
        legend_units=" Wh/m\u00b2",
        legend_title="Global Solar Radiation [Wh/m\u00b2]",
        legend_flags="t",
    )


def tpi(tools: Any, dem: str) -> None:
    """Calculate Topographic Position Index (TPI) and apply a color table."""
    print("Calculating Topographic Position Index (TPI)...")
    tools.r_tpi(input=dem, output="tpi")
    GeoColors.colors(maps=["tpi"], scheme_name="tpi", tools=tools, flags="e")

    aoi_map_figure(
        tools=tools,
        map_name="tpi",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_title="Topographic Position Index (TPI)",
        legend_flags="t",
    )


def landforms(tools: Any, dem: str, extra_shades: Any) -> None:
    """Compute landform classification and a simplified morphology raster."""
    print("Computing landforms...")
    tools.r_geomorphon(
        elevation=dem,
        forms=f"{dem}_landforms",
        search=21,
        skip=1,
        flat=1,
        dist=0,
    )

    aoi_map_figure(
        tools=tools,
        map_name=f"{LIDAR_DTM_1M}_landforms",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_flags="t",
        legend_title="Landforms",
        legend_orientation="vertical",
        shade_flags="n",
        extra_shades=extra_shades,
    )

    tools.r_param_scale(
        input=dem,
        out=f"{dem}_morphology",
        method="feature",
        size=5,
    )

    aoi_map_figure(
        tools=tools,
        map_name=f"{LIDAR_DTM_1M}_morphology",
        relief=LIDAR_DTM_1M_RELIEF,
        legend_flags="t",
        legend_title="Morphology",
        legend_orientation="vertical",
        shade_flags="n",
        extra_shades=extra_shades,
    )


def main():
    v = sys.version_info
    print(f"We are using Python {v.major}.{v.minor}.{v.micro}")
    _add_grass_to_syspath()
    _ensure_save_dir()

    # Import GRASS libraries (available after `_add_grass_to_syspath()`)
    import grass.script as gs
    from grass.tools import Tools
    from grass.exceptions import ScriptError

    # Workflow helpers are defined at module scope.

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
        install_grass_addons()

        # Import DSM and DTM at 1m resolution
        import_dem_data(res=10, tools=tools)

        # Set region and run analysis tools
        tools.g_region(raster=DTM_NAME, flags="a")

        # Set values below 0 to NULL
        set_ocean_to_null(tools, elevation_map=DTM_NAME)
        set_ocean_to_null(tools, elevation_map=DSM_NAME)
        set_ocean_to_null(tools, elevation_map=LIDAR_DTM_10M)

        # Set color tables
        ponui_island_color_scheme(tools, [DTM_NAME, DSM_NAME, LIDAR_DTM_10M])

        # Resample to 100m, 200m and 300m resolutions
        create_ocean_background(tools)
        resample_dem(tools=tools, dem=DTM_NAME, resolutions=[150, 250, 500])

        print("Computing relief...")
        tools.r_relief(input=DTM_NAME, output=DTM_RELIEF, quiet=True)

        # Create 1km grid for reference
        tools.v_mkgrid(map="grid_1k_1k", box="1000,1000")
        tools.v_extract(input="grid_1k_1k", cats=27, output=AOI_REGION)
        full_region_map_figure(
            tools=tools,
            map_name=DTM_NAME,
            relief=DTM_RELIEF,
            legend_units="m",
            legend_flags="bt"
        )

        # Compute second order derivatives and save results
        slope, aspect, pcurv, tcurv = compute_second_order_derivatives(
            tools=tools,
            dem=DTM_NAME
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
            res=1,
            flags="a"
        ):

            # Import LiDAR data and create a 1m DTM
            process_lidar_data(tools=tools)

            opt_rst = {
                "tension": 300,
                "smooth": 0.1,
                "npmin": 200,
                "dmin": 1.5,
                "flags": "t"
            }
            create_lidar_dem_rst(
                tools=tools,
                points="lidar_be",
                optimization=opt_rst
            )

            # prepare cartographic features.
            set_ocean_to_null(tools, elevation_map=LIDAR_DTM_1M)

            print("Computing skyview factor...")
            tools.r_skyview(
                input=LIDAR_DTM_1M,
                output=LIDAR_DTM_1M_SKYVIEW,
                ndir=8
            )
            ponui_island_color_scheme(tools, LIDAR_DTM_1M)
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

            # Color bare earth points per cell
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

            slope, aspect, pcurv, tcurv = compute_second_order_derivatives(
                tools=tools, dem=LIDAR_DTM_1M
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
                dem=LIDAR_DTM_1M,
                threshold=100000,
            )

            # Convert basins to vectors and extract basin 2
            tools.r_to_vect(
                input="d8_mfd_basins2",
                output="d8_mfd_basins2",
                type="area"
            )
            tools.v_extract(input="d8_mfd_basins2", cats="2", output="basin2")

            # Figure overlay options
            extra_vectors = [
                {
                    "map": "d8_mfd_basins2",
                    "type": "area",
                    "fill_color": "none",
                    "color": "#F5F5F5",
                    "width": 1,
                }
            ]

            extra_shades = [
                {
                    "color": LIDAR_DTM_1M,
                    "shade": LIDAR_DTM_1M_RELIEF,
                    "flags": "n",
                }
            ]

            # Calculate TWI
            twi_calculation(
                tools=tools,
                flow_accumulation="d8_mfd_flowaccum",
                slope=f"{LIDAR_DTM_1M}_slope"
            )

            # Delineate streams and watersheds
            stream_delineation(
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
                        "map": "stream_orders",
                        "type": "line",
                        "width_column": "horton",
                        "width_scale": 2

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
                        "map": "stream_orders",
                        "type": "line",
                        "width_column": "strahler",
                        "width_scale": 2
                    },
                ],
                extra_shades=extra_shades,
            )

            hand_method(
                tools,
                threshold=50000,
                extra_vectors=extra_vectors,
                extra_shades=extra_shades
            )
            tpi(tools, dem=LIDAR_DTM_1M)
            solar_radiation(tools)
            landforms(tools=tools, dem=LIDAR_DTM_1M, extra_shades=extra_shades)

            # Overland flow and erosion/deposition masked to basin
            print("Simulating overland flow and erosion/deposition...")
            with gs.MaskManager():
                tools.r_mask(vector="d8_mfd_basins2")

                # Overland flow simulation
                overland_flow(tools, elevation=LIDAR_DTM_1M)

                # Erosion and deposition
                erosion(tools, elevation=LIDAR_DTM_1M)

            # Overland-flow + erosion-deposition figures
            overland_and_erosion_figures = [
                (
                    "depth.30",
                    "Water Depth [m]",
                    "sl"
                ),
                (
                    "max_depth",
                    "Water Depth [m]",
                    "sl"
                ),
                (
                    "erosion_deposition",
                    "Erosion/Deposition [kg/m\u00b2s]",
                    "t"
                ),
                (
                    "transport_capacity",
                    "Transport Capacity [kg/m\u00b2s]",
                    "t"
                ),
                (
                    "tlimit_erosion_deposition",
                    "Transport Limited Erosion/Deposition [kg/m\u00b2s]",
                    "t"
                ),
                (
                    "sediment_flux",
                    "Sediment Flux [kg/m\u00b2s]",
                    "t",
                ),
                (
                    "sediment_concentration",
                    "Sediment Concentration [particle/m\u00b3]",
                    "t",
                ),
            ]
            for (
                map_name,
                legend_title,
                legend_flags,
            ) in overland_and_erosion_figures:
                aoi_map_figure(
                    tools=tools,
                    map_name=map_name,
                    relief=LIDAR_DTM_1M_RELIEF,
                    legend_flags=legend_flags,
                    legend_title=legend_title,
                    shade_flags="n",
                    extra_vectors=extra_vectors,
                    extra_shades=extra_shades,
                )

        # 3D figures. Each entry is the per-figure overrides for
        # `aoi_3d_figure` (defaults: elevation = LIDAR_DTM_1M,
        # output_name = mapcolor).
        aoi_3d_specs: list[dict] = [
            {"mapcolor": LIDAR_DTM_1M,
                "legend_units": "Elevation [m]"},
            {"mapcolor": f"{LIDAR_DTM_1M}_slope",
                "legend_units": "Slope [\u00b0]"},
            {"mapcolor": f"{LIDAR_DTM_1M}_aspect",
                "legend_units": "Aspect [\u00b0]"},
            {"mapcolor": f"{LIDAR_DTM_1M}_pcurv",
                "legend_units": "Profile Curvature"},
            {"mapcolor": f"{LIDAR_DTM_1M}_tcurv",
                "legend_units": "Tangential Curvature"},
            {"mapcolor": "max_depth",
                "legend_units": "Water Depth [m]", "legend_flags": "bsld"},
            {"mapcolor": "depth.30", "elevation": "depth.30",
                "legend_units": "Water Depth [m]", "legend_flags": "bsld"},
            {"mapcolor": "global_rad_172",
                "legend_units": "Global solar radiation [Wh/m\u00b2]"},
            {"mapcolor": "global_rad_356",
                "legend_units": "Global solar radiation [Wh/m\u00b2]"},
            {"mapcolor": "twi", "legend_units": "TWI"},
            {"mapcolor": "tpi", "output_name": "tpi",
                "legend_units": "TPI"},
            {"mapcolor": "d8_mfd_flowaccum",
                "output_name": "d8_mfd_flowaccum",
                "legend_units": "Flow Accumulation [D8 MFD]",
                "legend_flags": "blt", "legend_range_min": 1},
            {"mapcolor": "d8_sfd_flowaccum",
                "output_name": "d8_sfd_flowaccum",
                "legend_units": "Flow Accumulation [D8 SFD]",
                "legend_at": "12,17,8,47",
                "legend_flags": "blt", "legend_range_min": 1},
            {"mapcolor": "dinf_sfd_flowaccum",
                "output_name": "dinf_sfd_flowaccum",
                "legend_units": "Flow Accumulation [D-infinity SFD]",
                "legend_at": "12,17,8,47",
                "legend_flags": "btl", "legend_range_min": 1},
            {"mapcolor": "hand_class",
                "output_name": "hand_class",
                "legend_units": "Water Table Class",
                "legend_at": "12,17,8,47", "legend_flags": "btc"},
            {"mapcolor": "hand", "output_name": "hand",
                "legend_units": "Height above nearest drainage [m]",
                "legend_flags": "bdt"},
            {"mapcolor": "inundation_strds_3.0",
                "output_name": "inundation_strds_3.0",
                "legend_units": "Inundation [m]", "legend_flags": "bdt"},
        ]
        for spec in aoi_3d_specs:
            aoi_3d_figure(
                tools=tools,
                elevation=spec.get("elevation", LIDAR_DTM_1M),
                output_name=spec.get("output_name", spec["mapcolor"]),
                mapcolor=spec["mapcolor"],
                legend_units=spec.get("legend_units", ""),
                legend_at=spec.get("legend_at", "12,17,8,44"),
                legend_flags=spec.get("legend_flags", "btd"),
                legend_range_min=spec.get("legend_range_min"),
                legend_range_max=spec.get("legend_range_max"),
            )


if __name__ == "__main__":
    main()
