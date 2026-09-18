
#################################################################################
# MIT License

# Copyright (c) 2026 J.Boehner & O.Conrad

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#################################################################################


#################################################################################
#
# This script supplements the chapter
# "Land-surface parameters in climatology and meteorology"
# written by J.Boehner, Oleg Antonic, Shabeh ul Hasson
# (doi:10.1016/B978-0-44-333376-7.00018-5) from the text book
# "Geomorphometry: Concepts, Software, Applications"
# edited by Hannes I. Reuter, Carlos H. Grohmann, Vincent Lecours.
# 
# In order to run the script, you need to provide a recent SAGA installation
# (https://saga-gis.org). Under windows, the path to the PySAGA folder must
# also be configured (see below).
#
#################################################################################

#########################################
#---------------------------------------#
#           Initializations             #
#---------------------------------------#
#########################################

#########################################
#               PySAGA                  #
#_______________________________________#
# Windows: The most convenient way to make PySAGA available to your
# Python scripts is to add the path containing the PySAGA folder
# (i.e. the path to your SAGA installation) to the PYTHONPATH
# environment variable. You can do this from within your script
# with the following command (just uncomment the following line
# and adjust the path accordingly):
###import sys; sys.path.insert(1, 'C:/saga-9.12.0_x64')
#_________________________________________
from PySAGA import saga_api


#########################################
#       Initial Working Directory       #
#_______________________________________#
import os; os.chdir(os.path.dirname(__file__))


#########################################
#     Simple Exit-On-Error Routine      #
#_______________________________________#
def Exit_On_Error(Message):
    print('\n\n[ERROR] {:s}'.format(Message))
    import sys; sys.exit()


#########################################
#---------------------------------------#
#             DEM Creation              #
#---------------------------------------#
#########################################

#________________________________________
def Get_DEM_Basin(File, dem_island):
    dem = saga_api.SG_Get_Data_Manager().Add(File)
    if dem:
        return dem

    clipped = []
    from PySAGA.tools import grid_tools
    if grid_tools.Clip_Grids(GRIDS=[dem_island], CLIPPED=clipped, XMIN=1793351, XMAX=1795166, YMIN=5916484, YMAX=5917854):
        dem = saga_api.SG_Get_Data_Manager().Add(clipped[0])
        dem.Save(File)
        return dem

    saga_api.SG_Get_Data_Manager().Delete(dem)
    return None

#________________________________________
def Get_DEM_New_Zealand(File):
    dem = saga_api.SG_Get_Data_Manager().Add(File)
    if dem:
        return dem

    dem = saga_api.SG_Get_Data_Manager().Add_Grid()
    from PySAGA.tools import io_webservices
    if io_webservices.SRTM_CGIAR_CSI(RESULT=dem,
        XMIN=18529000, XMAX=19879000, YMIN=-5264000, YMAX=-3827000, CELLSIZE=1000,
        CRS_STRING='+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs +type=crs'): # targeted CRS is 'Equidistant Cylindrical' (aka 'Plate Carree')
        dem.Save(File)
        return dem

    saga_api.SG_Get_Data_Manager().Delete(dem)
    return None


#########################################
#---------------------------------------#
#########################################

#________________________________________
def Process_Fig3(dem):
    # [Basin]
    # Fig.3: Topographic direct solar radiation on June 21 (austral winter solstice) at 02, 03, and 04 pm
    # upper row: cast-shadowing included—lower row: cast-shadowing ignored

    from PySAGA.tools import ta_lighting

    direct = saga_api.SG_Get_Data_Manager().Add_Grid()

    for hour in [14., 15., 16.]:
        ta_lighting.Potential_Incoming_Solar_Radiation(GRD_DEM=dem, GRD_DIRECT=direct, PERIOD='moment',
            DAY='2026-06-21', MOMENT=hour)
        direct.Save('insolation_direct_2026-06-21_{:2.0f}00.tif'.format(hour))

        ta_lighting.Potential_Incoming_Solar_Radiation(GRD_DEM=dem, GRD_DIRECT=direct, PERIOD='moment',
            DAY='2026-06-21', MOMENT=hour, SHADOW='none')
        direct.Save('insolation_direct_2026-06-21_{:2.0f}00_no-shadow.tif'.format(hour))

#________________________________________
def Process_Fig4(dem, atmospheric_transmittance=60):
    # [Basin]
    # Fig.4: Topographic shortwave radiation on June 21 (austral winter solstice) at 04 pm
    # (a) Topographic direct solar radiation, (b) Topographic diffuse solar radiation, (c) Topographic land surface radiation

    from PySAGA.tools import ta_lighting

    direct  = saga_api.SG_Get_Data_Manager().Add_Grid()
    diffuse = saga_api.SG_Get_Data_Manager().Add_Grid()
    total   = saga_api.SG_Get_Data_Manager().Add_Grid()
    svf     = saga_api.SG_Get_Data_Manager().Add_Grid()
    ta_lighting.Sky_View_Factor(DEM=dem, SVF=svf)
    ta_lighting.Potential_Incoming_Solar_Radiation(GRD_DEM=dem, GRD_SVF=svf, GRD_DIRECT=direct, GRD_DIFFUS=diffuse, GRD_TOTAL=total,
        PERIOD='moment', DAY='2026-06-21', MOMENT=16., LUMPED=atmospheric_transmittance)
    direct .Save( 'insolation_direct_2026-06-21_1600.tif')
    diffuse.Save('insolation_diffuse_2026-06-21_1600.tif')
    total  .Save(  'insolation_total_2026-06-21_1600.tif')

#________________________________________
def Process_Fig5(dem, dates=['2026-12-21', '2026-06-21'], atmospheric_transmittance=60):
    # [Ponui Island]
    # Fig.5: Spatial distribution of potential topographic net shortwave radiation for Ponui Island
    # (a) 21 December (austral summer solstice), (b) 21 June (austral winter solstice).

    from PySAGA.tools import ta_lighting

    svf = saga_api.SG_Get_Data_Manager().Add_Grid()
    ta_lighting.Sky_View_Factor(DEM=dem, SVF=svf, RADIUS=1000)

    for date in dates:
        total = saga_api.SG_Get_Data_Manager().Add_Grid()
        ta_lighting.Potential_Incoming_Solar_Radiation(GRD_DEM=dem, GRD_SVF=svf, GRD_TOTAL=total,
            PERIOD='day', DAY=date, LUMPED=atmospheric_transmittance)
        total.Set_Scaling(1000. / 24.) # [kWh/m2] >> [W/m2]
        total.Save('net_shortwave_radiation_{}.tif'.format(date))

#________________________________________
def Process_Fig7and8(dem):
    # [New Zealand]
    # Fig.7: Topography vs. temperature distribution in New Zealand-Topography (a)
    # and spatial distribution of mean daily temperature in January (b) and July (c),
    # 1981-2010 long-term means (Karger et al., 2017).

    # [New Zealand]
    # Fig.8: Topography vs. vapour pressure distribution in New Zealand-Topography (a),
    # and spatial distribution of mean daily vapour pressure in January (b) and July (c),
    # 1981-2010 long-term means (Karger et al., 2017).

    from PySAGA.tools import io_webservices, grid_tools, climate_tools

    grids = []

    io_webservices.CHELSA__Global_Climate_Data(GRIDS=grids, EXTENT='grid system extent', GRID=dem,
        DATASET='climatology', PERIOD='1981-2010', VAR_CLIMATE='Daily Mean Near-Surface Air Temperature'
    )
    grid_tools.Grid_Masking(MASK=dem, GRIDS=grids, LIST=True)

    Tjan = grids[0].asGrids().Get_Grid(0)
    Tjul = grids[0].asGrids().Get_Grid(6)

    io_webservices.CHELSA__Global_Climate_Data(GRIDS=grids, EXTENT='grid system extent', GRID=dem,
        DATASET='climatology', PERIOD='1981-2010', VAR_CLIMATE='Near-Surface Relative Humidity'
    )
    grid_tools.Grid_Masking(MASK=dem, GRIDS=grids, LIST=True)

    RHjan = grids[0].asGrids().Get_Grid(0)
    RHjul = grids[0].asGrids().Get_Grid(6)

    VPjan = saga_api.SG_Get_Data_Manager().Add_Grid()
    VPjul = saga_api.SG_Get_Data_Manager().Add_Grid()

    climate_tools.Air_Humidity_Conversions(CONVERSION='Relative Humidity', T=Tjan, IN_RH=RHjan, OUT_VP=VPjan)
    climate_tools.Air_Humidity_Conversions(CONVERSION='Relative Humidity', T=Tjul, IN_RH=RHjul, OUT_VP=VPjul)

    Tjan.Save('nz_chelsa_tmean_1981-2010_jan.tif'); VPjan.Save('nz_chelsa_vp_1981-2010_jan.tif'); RHjan.Save('nz_chelsa_rh_1981-2010_jan.tif')
    Tjul.Save('nz_chelsa_tmean_1981-2010_jul.tif'); VPjul.Save('nz_chelsa_vp_1981-2010_jul.tif'); RHjul.Save('nz_chelsa_rh_1981-2010_jul.tif')

#________________________________________
def Process_Fig9(dem):
    # [Basin]
    # Fig.9: Land Surface Parameters effecting temperature and moisture distribution
    # (a) diurnal anisotropic heating (αmax = 202.5°), (b) relative slope position, and (c) delineated relative vertical distance to mid-slope position.

    from PySAGA.tools import ta_morphometry

    dah = saga_api.SG_Get_Data_Manager().Add_Grid()
    ta_morphometry.Diurnal_Anisotropic_Heat(DEM=dem, DAH=dah, ALPHA_MAX=202.5)
    dah.Save('diurnal_anisotropic_heating.tif')

    rsp = saga_api.SG_Get_Data_Manager().Add_Grid()
    msp = saga_api.SG_Get_Data_Manager().Add_Grid()
    ta_morphometry.Relative_Heights_and_Slope_Positions(DEM=dem, NH=rsp, MS=msp)
    rsp.Save('relative_slope_position.tif')
    msp.Save('mid_slope_position.tif')

#________________________________________
def Process_Fig10(dem):
    # [Ponui Island]
    # Fig.10: Wind Exposition Index (WEI) for wind direction southwest (a)
    # and averaged over the full circle at an angle increment of 15° (b).

    from PySAGA.tools import ta_morphometry

    wei = saga_api.SG_Get_Data_Manager().Add_Grid()

    # wind is blowing from SW (225°), but tool wants direction to which the wind blows (225°-180°=45°)!
    ta_morphometry.Wind_Effect_Windward__Leeward_Index(DEM=dem, EFFECT=wei, DIR=45)
    wei.Save('wei_from_southwest.tif')

    ta_morphometry.Wind_Exposition_Index(DEM=dem, EXPOSITION=wei, STEP=15)
    wei.Save('wei_full.tif')

#________________________________________
def Process_Fig11(dem):
    # [New Zealand]
    # Fig.11: Topographic exposure vs. precipitation distribution in New Zealand
    # Windward-Leeward Index (WLI) for advection direction west (a) and spatial distribution of mean monthly precipitation in January (b) and July (c),
    # 1981-2010 long-term means (Karger et al., 2017).

    from PySAGA.tools import ta_morphometry, io_webservices, grid_tools

    wei = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_morphometry.Wind_Effect_Windward__Leeward_Index(DEM=dem, EFFECT=wei, DIR=90)
    wei.Save('nz_wei_from_west.tif')

    grids = []

    io_webservices.CHELSA__Global_Climate_Data(GRIDS=grids, EXTENT='grid system extent', GRID=dem,
        DATASET='climatology', PERIOD='1981-2010', VAR_CLIMATE='Precipitation'
    )
    grid_tools.Grid_Masking(MASK=dem, GRIDS=grids, LIST=True)

    grids[0].asGrids().Get_Grid(0).Save('nz_chelsa_p_1981-2010_jan.tif')
    grids[0].asGrids().Get_Grid(6).Save('nz_chelsa_p_1981-2010_jul.tif')


#########################################
#---------------------------------------#
#                 main                  #
#---------------------------------------#
#########################################

#########################################
#________________________________________
if __name__ == '__main__':
    print('\nLand-surface parameters in climatology and meteorology\n')

    if saga_api.SG_Compare_SAGA_Version(9, 11, 0) > 0:
        # parts of this script require tools (in particular the downloaders for SRTM and CHELSA) not available in older SAGA versions
        Exit_On_Error('Required SAGA version is at least 9.11 (currently running: {})! Please update!'.format(saga_api.SAGA_VERSION))

    os.chdir(os.path.dirname(__file__))

    # Uncomment the following line to suppress processing message output:
    # saga_api.SG_UI_ProgressAndMsg_Lock(True)

    #____________________________________
    dem_island = saga_api.SG_Get_Data_Manager().Add('dtm_05m_ponui_island.tif')
    if not dem_island:
        Exit_On_Error('Failed to load DEM (Ponui Island)')

    dem_basin  = Get_DEM_Basin('dtm_05m_ponui_basin.tif', dem_island)
    if not dem_basin:
        Exit_On_Error('Failed to load DEM (Basin)')

    dem_nz     = Get_DEM_New_Zealand('SRTM (CGIAR CSI) New Zealand (1000m).tif')
    if not dem_nz:
        Exit_On_Error('Failed to load DEM (New Zealand)')

    #____________________________________
    dir_work = os.path.dirname(__file__) + '/results'
    if not os.path.exists(dir_work):
        os.makedirs(dir_work)
    os.chdir(dir_work)

    #____________________________________
    Process_Fig3     (dem_basin)
    Process_Fig4     (dem_basin)
    Process_Fig5     (dem_island)
    Process_Fig7and8 (dem_nz)
    Process_Fig9     (dem_basin)
    Process_Fig10    (dem_island)
    Process_Fig11    (dem_nz)

    #____________________________________
    print('\n_____\nfinished processing!')


#########################################
#________________________________________

#########################################
#---------------------------------------#
#                 end                   #
#---------------------------------------#
#########################################
