
#################################################################################
# MIT License

# Copyright (c) 2024 Olaf Conrad, Volker Wichmann

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
# This script supplements the chapter "Geomorphometry in SAGA" from the
# Geomorphometry book and generates the data sets presented there for
# Ponui Island. This script has been worked out with SAGA 9.7.
# 
# In order to run the script, the path to the input LAS file must be adjusted
# in the "Globals" section. Under windows, the path to the PySAGA folder must
# also be configured (see below).
#
# The script defines some helper functions as well as several processing
# functions for (i) DEM creation from the point cloud, (ii) contour line
# calculation, (iii) morphometric analysis, (iv) relief classification
# and (v) hydological analysis. The processing functions are called by the
# main function that is executed when the script is started.
#
#################################################################################

#########################################
#---------------------------------------#
#           Importing PySAGA            #
#---------------------------------------#
#########################################

#_________________________________________
##########################################
# Windows: The most convenient way to make PySAGA available to your
# Python scripts is to add the path containing the PySAGA folder
# (i.e. the path to your SAGA installation) to the PYTHONPATH
# environment variable. You can do this from within your script
# with the following command (just uncomment the following line
# and adjust the path accordingly):
###import sys; sys.path.insert(1, 'C:/saga-9.7.0_x64')

#_________________________________________
from PySAGA import saga_api


#########################################
#---------------------------------------#
#                Globals                #
#---------------------------------------#
#########################################

#########################################
#________________________________________
import os

las_file = 'C:/Ponui Island/ponui.laz'
las_epsg = 2193
dir_work = os.path.dirname(__file__)

#________________________________________
fmt_raster = 'tif'     # tif / sg-grd-z
fmt_vector = 'geojson' # shp / gpkg / geojson


#########################################
#---------------------------------------#
#           Helper Functions            #
#---------------------------------------#
#########################################

#########################################
# Simple Exit-On-Error Routine
#________________________________________
def Exit_On_Error(Message):
    print('\n\n[ERROR] {:s}'.format(Message))
    import sys; sys.exit()


#########################################
# Save Data
#________________________________________
def Save_Data(Data, Name=None, Delete=False):
    if not Name:
        Name = Data.Get_Name()

    if   Data.Get_ObjectType() == saga_api.SG_DATAOBJECT_TYPE_Grid:
        Extension = fmt_raster
    elif Data.Get_ObjectType() == saga_api.SG_DATAOBJECT_TYPE_Shapes:
        Extension = fmt_vector
    elif Data.Get_ObjectType() == saga_api.SG_DATAOBJECT_TYPE_PointCloud:
        Extension = 'sg-pts-z'
    else:
        return False

    saga_api.SG_UI_ProgressAndMsg_Lock(True)
    Result = Data.Save('{:s}/{:s}.{:s}'.format(dir_work, Name, Extension))
    saga_api.SG_UI_ProgressAndMsg_Lock(False)

    if Delete: # free memory resources ?
        saga_api.SG_Get_Data_Manager().Delete(Data)

    return Result


#########################################
#---------------------------------------#
#             DEM Creation              #
#---------------------------------------#
#########################################

#########################################
#________________________________________
def Create_DTM_from_PointCloud(LAS_File, LAS_EPSG=0, Cellsize=1., DirectGridding=False, SaveDTMwithGaps=False, SaveDTMSplined=True, CreateDSMHeight=True, KeepPointsInMemory=False, Resamples=[], Verbose=False):

    print('\n_____\nprocessing {:.1f}m target resolution...\n'.format(Cellsize))

    from PySAGA.tools import io_pdal, grid_spline, grid_tools, grid_calculus, ta_preprocessor

    if not Verbose:
        saga_api.SG_UI_ProgressAndMsg_Lock(True)


    #####################################
    # Gridding of points with optional gap filling
    #____________________________________
    def PointCloud_to_Grid(Points, Cellsize, Aggregation='mean', CloseGapsRadius=0.):
        from math import floor, ceil; from PySAGA.tools import grid_gridding

        grid = saga_api.SG_Get_Data_Manager().Add_Grid()
        if not grid_gridding.Shapes_to_Grid(GRID=grid, INPUT=Points, FIELD='Z', MULTIPLE=Aggregation, GRID_TYPE='4 byte floating point number', TARGET_USER_SIZE=Cellsize,
                TARGET_USER_XMIN=floor(Points.Get_Extent().xMin / Cellsize) * Cellsize,
                TARGET_USER_XMAX=ceil (Points.Get_Extent().xMax / Cellsize) * Cellsize,
                TARGET_USER_YMIN=floor(Points.Get_Extent().yMin / Cellsize) * Cellsize,
                TARGET_USER_YMAX=ceil (Points.Get_Extent().yMax / Cellsize) * Cellsize):
            Exit_On_Error('gridding of points')

        CloseGapsRadiusCells = int(0.5 + CloseGapsRadius / Cellsize)
        if CloseGapsRadiusCells > 0:
            grid_tools.Shrink_and_Expand(INPUT=grid, OPERATION='expand and shrink', RADIUS=CloseGapsRadiusCells, EXPAND='mean')

        return grid


    #####################################
    # Create elevation models from point cloud elevations...
    #____________________________________

    # LAS File Format Classification Value Meaning
    #   0 Created, Never Classified
    #   1 Unclassified
    #   2 Ground
    #   3 Low Vegetation
    #   4 Medium Vegetation
    #   5 High Vegetation
    #   6 Building
    #   7 Low Point (Noise)
    #   8 Model Key-Point (Mass Point)
    #   9 Water
    #  12 Overlap Points
    # (source: https://www.asprs.org/divisions-committees/lidar-division/laser-las-file-format-exchange-activities)

    if not DirectGridding:

        print('\ndigital surface model...')

        #________________________________
        # Import the original LAZ file (if not done yet).
        # The function doing the job will only keep valid
        # points following the LAS specification for the
        # classification flag. For later use the imported
        # points will be stored using SAGA's compressed
        # point cloud format (*.sg-pts-z).

        file   = saga_api.CSG_String('{:s}/{:s}.sg-pts-z'.format(dir_work, 'points'))
        points = saga_api.SG_Get_Data_Manager().Find(file) # already loaded ?
        if not points:
            points = saga_api.SG_Get_Data_Manager().Add(file) # already created ?
            if not points:
                list = [] # Python list, will become filled after successful execution with output data objects of type 'saga_api.CSG_PointCloud'
                if not io_pdal.Import_Point_Cloud(FILES=LAS_File, POINTS=list, VARS=False, VAR_INTENSITY=True, VAR_CLASSIFICATION=True, CLASSES='2,3,4,5,6'):
                    Exit_On_Error('loading LAS file\n\t\'{:s}\''.format(LAS_File))
                points = saga_api.SG_Get_Data_Manager().Add(list[0]) # add point cloud to the data manager
                if LAS_EPSG > 0:
                    points.Get_Projection().Create(LAS_EPSG)
                if not Verbose: # let the user know about the progress
                    saga_api.SG_UI_ProgressAndMsg_Lock(False)
                points.Save(file) # store result for an easy reload (SAGA compressed point cloud format)
                if not Verbose:
                    saga_api.SG_UI_ProgressAndMsg_Lock(True)

        #________________________________
        # Create a Digital Surface Model (DSM)
        # Simply assigns each point's z value to the raster
        # cell containing the point's location. In case that
        # multiple points belong to the same cell the maximum
        # z value will be kept thus reflecting mostly the
        # vegetation/building elevation and not the ground.
        # The function called here optionally allows to close
        # (small) gaps within the scanned area using a 'expand
        # and shrink' operation. The maximum expansion distance
        # is supplied in map units (here 12. meters).

        dsm = PointCloud_to_Grid(points, Cellsize, 'maximum', 12.)

        if not KeepPointsInMemory:
            saga_api.SG_Get_Data_Manager().Delete(points)

        #________________________________
        # Extract ground points (if not done yet)
        # Following the LAS specification the classification
        # attribute of ground points is set to the value '2'.
        # Again, for an easy reload the extracted ground points
        # will be stored using SAGA's compressed point cloud
        # format (*.sg-pts-z).

        print('\ndigital terrain model...')

        file   = saga_api.CSG_String('{:s}/{:s}.sg-pts-z'.format(dir_work, 'points_ground'))
        ground = saga_api.SG_Get_Data_Manager().Find(file) # already loaded ?
        if not ground:
            ground = saga_api.SG_Get_Data_Manager().Add(file) # already created ?
            if not ground:
                list = [] # Python list, will become filled after successful execution with output data objects of type 'saga_api.CSG_PointCloud'
                if not io_pdal.Import_Point_Cloud(FILES=LAS_File, POINTS=list, VARS=False, VAR_INTENSITY=True, CLASSES='2'):
                    Exit_On_Error('loading LAS file\n\t\'{:s}\''.format(LAS_File))
                ground = saga_api.SG_Get_Data_Manager().Add(list[0]) # add point cloud to the data manager
                if LAS_EPSG > 0:
                    ground.Get_Projection().Create(LAS_EPSG)
                if not Verbose: # let the user know about the progress
                    saga_api.SG_UI_ProgressAndMsg_Lock(False)
                ground.Save(file) # store result for an easy reload (SAGA compressed point cloud format)
                if not Verbose:
                    saga_api.SG_UI_ProgressAndMsg_Lock(True)

        #________________________________
        # Create a Digital Terrain Model (DTM)
        # Same operation used for DSM creation except that we
        # only use those points being classified as ground and
        # instead of multiple points belonging to one cell
        # we take the mean elevation. Dependent on the point
        # density and the chosen cell size it is very likely
        # that the result will have gaps particularly due to
        # dense vegetation and buildings (no ground signal).

        dtm = PointCloud_to_Grid(ground, Cellsize, 'mean')

        if not KeepPointsInMemory:
            saga_api.SG_Get_Data_Manager().Delete(ground)

    #____________________________________
    else: # DirectGridding == True
        print('\ndigital surface model...')

        dsm = saga_api.SG_Get_Data_Manager().Add_Grid()
        if not io_pdal.Import_Grid_from_Point_Cloud(FILES=LAS_File, GRID=dsm, CLASSES='2,3,4,5,6', AGGREGATION='maximum', TARGET_DEFINITION='user defined', TARGET_USER_SIZE=Cellsize):
            Exit_On_Error('importing grid from point cloud')

        if LAS_EPSG > 0:
            dsm.Get_Projection().Create(LAS_EPSG)

        print('\ndigital terrain model...')

        dtm = saga_api.SG_Get_Data_Manager().Add_Grid()
        if not io_pdal.Import_Grid_from_Point_Cloud(FILES=LAS_File, GRID=dtm, CLASSES='2', AGGREGATION='mean', TARGET_DEFINITION='grid or grid system', TARGET_TEMPLATE=dsm):
            Exit_On_Error('importing grid from point cloud')

        if LAS_EPSG > 0:
            dtm.Get_Projection().Create(LAS_EPSG)

    #____________________________________
    # Storing gridded DEMs.

    Save_Data(dsm, 'dsm_{:02.0f}m'.format(Cellsize))

    if SaveDTMwithGaps:
        Save_Data(dtm, 'dtm_{:02.0f}m_with-gaps'.format(Cellsize))

    #____________________________________
    # Create a gap-free DTM using a spline interpolation.

    dtm_splined = saga_api.SG_Get_Data_Manager().Add_Grid()
    dtm_splined.Create(dtm.Get_System())

    if not grid_spline.Multilevel_BSpline_from_Grid_Points(GRID=dtm, TARGET_OUT_GRID=dtm_splined, TARGET_DEFINITION='grid or grid system'):
        Exit_On_Error('creating splined ground elevations')

    if not grid_tools.Grid_Masking(GRID=dtm_splined, MASK=dsm):
        Exit_On_Error('applying mask to splined ground elevations')

    if not grid_tools.Patching(ORIGINAL=dtm, ADDITIONAL=dtm_splined, RESAMPLING='Nearest Neighbour'):
        Exit_On_Error('patching gaps in DTM with splined ground elevations')

    if SaveDTMSplined:
        Save_Data(dtm_splined, 'dtm_{:02.0f}m_splined'.format(Cellsize))
    saga_api.SG_Get_Data_Manager().Delete(dtm_splined)

    Save_Data(dtm, 'dtm_{:02.0f}m'.format(Cellsize))

    print('\nfurther processing...')

    #____________________________________
    # Calculate the height of vegetation/buildings above ground

    if CreateDSMHeight:
        difference = saga_api.SG_Get_Data_Manager().Add_Grid()
        if not grid_calculus.Grid_Difference(A=dsm, B=dtm, C=difference):
            Exit_On_Error('difference calculation')
        Save_Data(difference, 'dsm_{:02.0f}m_height'.format(Cellsize), Delete=True)

    #____________________________________
    # Create resampled grids for requested cellsizes
    for cellsize in Resamples:
        if( cellsize > 0. and cellsize != Cellsize ):
            grids = [] # Python list, will become filled after successful execution with output data objects of type 'saga_api.CSG_Grid'
            if not grid_tools.Resampling(INPUT=[dtm, dsm], OUTPUT=grids, TARGET_USER_SIZE=cellsize):
                Exit_On_Error('resampling')

            if CreateDSMHeight:
                difference = saga_api.SG_Get_Data_Manager().Add_Grid()
                if not grid_calculus.Grid_Difference(A=grids[1], B=grids[0], C=difference):
                    Exit_On_Error('difference calculation')
                Save_Data(difference, 'dsm_{:02.0f}m_height'.format(cellsize), Delete=True)

            Save_Data(grids[0], 'dtm_{:02.0f}m'.format(cellsize), Delete=True)
            Save_Data(grids[1], 'dsm_{:02.0f}m'.format(cellsize), Delete=True)

    #____________________________________
    if KeepPointsInMemory:
        saga_api.SG_Get_Data_Manager().Delete(dsm)
        saga_api.SG_Get_Data_Manager().Delete(dtm)
    else:
        saga_api.SG_Get_Data_Manager().Delete() # remove any data objects from memory

    if not Verbose:
        saga_api.SG_UI_ProgressAndMsg_Lock(False)

    return True


#########################################
#---------------------------------------#
#        Terain Analysis Receipes       #
#---------------------------------------#
#########################################

#########################################
# Contour Lines
#________________________________________
def Contour(DTM, Intervals=[10., 50.], Scale=1., Verbose=1):
    print('\n_____\nprocessing contour lines...')

    from PySAGA.tools import shapes_grid

    Contour = saga_api.SG_Get_Data_Manager().Add_Shapes()

    for Interval in Intervals:
        if not shapes_grid.Contour_Lines_from_Grid(GRID=DTM, CONTOUR=Contour, ZSTEP=Interval, SCALE=Scale, Verbose=Verbose):
            Exit_On_Error('contour lines')
        Save_Data(Contour, '{:s} [Interval {:.0f}]'.format(DTM.Get_Name(), Interval))

    saga_api.SG_Get_Data_Manager().Delete(Contour)


#########################################
# Morphometric Analysis
#________________________________________
def Morphometry(DTM, Verbose=1):
    print('\n_____\nprocessing morphometry...')

    from PySAGA.tools import ta_lighting, ta_morphometry

    #____________________________________
    # Analytical Hillhading

    Shading = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_lighting.Analytical_Hillshading(ELEVATION=DTM, SHADE=Shading, METHOD='Ambient Occlusion', Verbose=Verbose)

    Save_Data(Shading, Delete=True)

    #____________________________________
    # Slope, Aspect, Curvature

    slope  = saga_api.SG_Get_Data_Manager().Add_Grid()
    aspect = saga_api.SG_Get_Data_Manager().Add_Grid()
    c_plan = saga_api.SG_Get_Data_Manager().Add_Grid()
    c_prof = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_morphometry.Slope_Aspect_Curvature(ELEVATION=DTM, SLOPE=slope, ASPECT=aspect, C_PROF=c_prof, C_PLAN=c_plan, Verbose=Verbose)

    Save_Data(slope , Delete=True)
    Save_Data(aspect, Delete=True)
    Save_Data(c_prof, Delete=True)
    Save_Data(c_plan, Delete=True)

    #____________________________________
    # Topographic Openness

    pos = saga_api.SG_Get_Data_Manager().Add_Grid()
    neg = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_lighting.Topographic_Openness(DEM=DTM, POS=pos, NEG=neg, Verbose=Verbose)

    Save_Data(pos, Delete=True)
    Save_Data(neg, Delete=True)

    #____________________________________
    # Topographic Openness

    tpi = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_morphometry.Topographic_Position_Index_TPI(DEM=DTM, TPI=tpi, Verbose=Verbose)

    Save_Data(tpi, Delete=True)


#########################################
# Relief Classification
#________________________________________
def Classification(DTM, Verbose=1):
    print('\n_____\nprocessing morphometry...')

    from PySAGA.tools import ta_morphometry, ta_lighting

    Classes = saga_api.SG_Get_Data_Manager().Add_Grid()

    #____________________________________
    ta_morphometry.Curvature_Classification(DEM=DTM, CLASSES=Classes, STRAIGHT=175.0, VERTICAL='longitudinal curvature', SMOOTH=16/DTM.Get_Cellsize(), Verbose=Verbose)
    Save_Data(Classes, 'Classes.Curvature')

    ta_lighting.Geomorphons(DEM=DTM, GEOMORPHONS=Classes, RADIUS=150.0, Verbose=Verbose)
    Save_Data(Classes, 'Classes.Geomorphons')

    ta_morphometry.TPI_Based_Landform_Classification(DEM=DTM, LANDFORMS=Classes, RADIUS_A='0; 25', RADIUS_B='0; 150', Verbose=Verbose)
    Save_Data(Classes, 'Classes.TopographicPositionIndex')

    ta_morphometry.Morphometric_Features(DEM=DTM, FEATURES=Classes, SIZE=10, TOL_SLOPE=10.0, TOL_CURVE=0.005, CONSTRAIN=True, Verbose=Verbose)
    Save_Data(Classes, 'Classes.MorphometricFeatures')

    #____________________________________
    saga_api.SG_Get_Data_Manager().Delete(Classes)


#########################################
# Hydrologic Analysis
#________________________________________
def Hydrology(DTM, Verbose=1):
    print('\n_____\nprocessing hydrology...')

    from PySAGA.tools import ta_preprocessor, ta_hydrology, ta_channels

    #____________________________________
    # remove spurious pits

    dtm_nosinks = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_preprocessor.Fill_Sinks_XXL_Wang_and_Liu(ELEV=DTM, FILLED=dtm_nosinks, MINSLOPE=0.1, Verbose=Verbose)

    Save_Data(dtm_nosinks, DTM.Get_Name() + ' [no sinks]')

    #____________________________________
    # flow accumulation

    flow = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_hydrology.Flow_Accumulation_TopDown(ELEVATION=dtm_nosinks, FLOW=flow, METHOD='Multiple Flow Direction', Verbose=Verbose)

    Save_Data(flow)

    #____________________________________
    # topographic wetness index

    twi = saga_api.SG_Get_Data_Manager().Add_Grid()

    ta_hydrology.SAGA_Wetness_Index(DEM=dtm_nosinks, TWI=twi, Verbose=Verbose)

    Save_Data(twi)

    #____________________________________
    # channel network and drainage basins

    channels = saga_api.SG_Get_Data_Manager().Add_Shapes()
    basins   = saga_api.SG_Get_Data_Manager().Add_Shapes()

    ta_channels.Channel_Network_and_Drainage_Basins(DEM=dtm_nosinks, SEGMENTS=channels, BASINS=basins, THRESHOLD=5, SUBBASINS=False, Verbose=Verbose)

    Save_Data(channels, 'channels')
    Save_Data(basins  , 'basins'  )


#########################################
#---------------------------------------#
#                 main                  #
#---------------------------------------#
#########################################

#########################################
#________________________________________
if __name__ == '__main__':
    dir_work = os.path.dirname(__file__) + '/results'
    if not os.path.exists(dir_work):
        os.makedirs(dir_work)

    #____________________________________
    # DEM Creation

    if False:
        # create each target resolution directly from points data
        Create_DTM_from_PointCloud(las_file, las_epsg,  1., KeepPointsInMemory=True)
        Create_DTM_from_PointCloud(las_file, las_epsg,  2., KeepPointsInMemory=True)
        Create_DTM_from_PointCloud(las_file, las_epsg,  5., KeepPointsInMemory=True)
        Create_DTM_from_PointCloud(las_file, las_epsg, 10.)
    elif False:
        # only create highest target resolution directly from points data and coarser resolutions by resampling from this
        Create_DTM_from_PointCloud(las_file, las_epsg,  1., Resamples=[2., 5., 10.])
    else:
        # like previous but without loading the point clouds into memory (less memory consuming)
        Create_DTM_from_PointCloud(las_file, las_epsg,  5., DirectGridding=True)

    #____________________________________
    # Terrain Analysis

    print('\ndigital terrain analysis...')

    file = '{:s}/dtm_{:02.0f}m.{:s}'.format(dir_work, 5., fmt_raster)
    dtm = saga_api.SG_Get_Data_Manager().Add_Grid(file)
    if not dtm:
        Exit_On_Error('failed to load \'{:s}\''.format(file))

    Contour(dtm)
    Morphometry(dtm)
    Classification(dtm)
    Hydrology(dtm)

    #____________________________________
    print('\n_____\nfinished processing!')


#########################################
#________________________________________

#########################################
#---------------------------------------#
#                 end                   #
#---------------------------------------#
#########################################
