
import arcpy
import os.path import basename, dirname
from arcpy.sa import NbrAnnulus, NbrCircle, FocalStatistics


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Derivative calculator"
        self.alias = "DEV calculator"
        self.description = ""

        # List of tool classes associated with this toolbox which will appear on the Catalog
        self.tools = [DEV_calculator]

# We add an external class, “helpers”, which will not appear on the interface of the toolbox but which contains a single function that helps with corollary operations. In this case the function that converts back-slashes (accepted through the ArcGIS tool) to forward-slashes (needed in python script) in a path
class helpers(object):
    
    def convert_backslash_forwardslash(self,inText):
        
        inText = fr"{inText}"
        if inText.find('\t'):
            inText = inText.replace('\t', '\\t')
        elif inText.find('\n'):
            inText = inText.replace('\n', '\\n')
        elif inText.find('\r'):
            inText = inText.replace('\r', '\\r')

        inText = inText.replace('\\','/')
        return inText

# We define the tool class within our custom toolbox with its internal functions
class DEV_calculator(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Mean LTPs"
        self.description = "A toolbox to calculate the relative deviation from mean value of a central cell"
        self.canRunInBackground = False


    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Input terrain raster",# This appears in the dialog box
            name="input_dtm",
            datatype="GPRasterLayer",# Data type for raster files
            parameterType="Required",",# It can also be set as “optional”
            direction="Input")
        
        param1 = arcpy.Parameter(
            displayName="Inner radius (unit: cell)",
            name="inner_radius",
            datatype="GPLong",# Data type for an integer
            parameterType="Required",
            direction="Input")
        param1.value = 3 # This is a default parameter
        
        param2 = arcpy.Parameter(
            displayName="Outer radius (unit: cell)",
            name="outer_radius",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param2.value = 5 
        
        param3 = arcpy.Parameter(
            displayName="Output position index",
            name="out_raster",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output")
        
        parameters = [param0, param1, param2, param3]
        
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        
        if parameters[0].valueAsText is not None:
            folder = basename(dirname(parameters[0].valueAsText))
            if folder.lower().endswith(('.gdb', '.mdb')):
                parameters[0].setErrorMessage("Geodatabases cannot be used in this toolbox")
                
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        arcpy.env.overwriteOutput = True # enable overwriting
        input_dtm = parameters[0].valueAsText # load the variables from the parameter list
        inner_radius = parameters[1].valueAsText
        outer_radius = parameters[2].valueAsText
        out_raster = parameters[3].valueAsText
        
        helper = helpers() # enable the functions in the “helper” class
        
        input_dtm = helper.convert_backslash_forwardslash(input_dtm)
        out_raster = helper.convert_backslash_forwardslash(out_raster)
        
        if input_dtm.rfind("/") < 0: #apply helper to a loaded layer in the project
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            m = aprx.activeMap            
            for lyr in m.listLayers():
                if lyr.isRasterLayer:
                    if input_dtm == lyr.name: 
                        input_dtm = helper.convert_backslash_forwardslash(lyr.dataSource)
        
        #Run the procedure to calculate DEV. First establish the neighborhood type, then calculate the focal statistics with the distance requested, and finally the DEV.
        if int(inner_radius) > 0:
            neighborhood = NbrAnnulus(inner_radius, outer_radius, "CELL")
            
        else:
            neighborhood = NbrCircle(outer_radius, "CELL")
        
        out_focal_statistics = FocalStatistics(input_dtm, neighborhood, "MEAN")
        std_dev = FocalStatistics(input_dtm, neighborhood, "STD")
        
        result_raster = (input_dtm - out_focal_statistics) / std_dev
        
        result_raster.save(out_raster) 
        
        return
