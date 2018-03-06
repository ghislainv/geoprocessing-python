from osgeo import osr, ogr, gdal
import numpy as np

# ===============================================
# Filter a shapefile
# ===============================================
# https://joeahand.com/archive/filtering-a-shapefile-with-python/


def create_filtered_shapefile(value, filter_field, in_shapefile,
                              out_shapefile):
    input_ds = ogr.Open(in_shapefile)
    input_layer = input_ds.GetLayer()

    # Filter by our query
    query_str = "{} = '{}'".format(filter_field, value)
    input_layer.SetAttributeFilter(query_str)

    # Copy Filtered Layer and Output File
    driver = ogr.GetDriverByName("ESRI Shapefile")
    out_ds = driver.CreateDataSource(out_shapefile)
    out_layer = out_ds.CopyLayer(input_layer, str(value))
    del input_layer, out_layer, out_ds
    return out_shapefile


# Filter
create_filtered_shapefile("Africa", "CONTINENT",
                          "continents/continent.shp", "continents/africa.shp")

# It works also with ogr2ogr command
# os.system("ogr2ogr -f 'ESRI Shapefile' -where \"CONTINENT = 'Africa'\" \
# continents/africa.shp continents/continent.shp")

# ===============================================
# Reproject layer
# ===============================================
# https://pcjericks.github.io/py-gdalogr-cookbook/projection.html#reproject-a-layer

driver = ogr.GetDriverByName("ESRI Shapefile")

# input SpatialReference
inSpatialRef = osr.SpatialReference()
inSpatialRef.ImportFromEPSG(4326)

# output SpatialReference
aea_proj = "+proj=aea +lat_1=20 +lat_2=-23 +lat_0=0 +lon_0=25 +x_0=0 +y_0=0 \
+ellps=WGS84 +datum=WGS84 +units=m no_defs"
outSpatialRef = osr.SpatialReference()
outSpatialRef.ImportFromProj4(aea_proj)

# create the CoordinateTransformation
coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

# get the input layer
inDataSet = driver.Open("continents/africa.shp")
inLayer = inDataSet.GetLayer()

# create the output layer
outputShapefile = "continents/africa_aea.shp"
outDataSet = driver.CreateDataSource(outputShapefile)
outLayer = outDataSet.CreateLayer("africa_aea", srs=outSpatialRef,
                                  geom_type=ogr.wkbMultiPolygon)

# add fields
inLayerDefn = inLayer.GetLayerDefn()
for i in range(0, inLayerDefn.GetFieldCount()):
    fieldDefn = inLayerDefn.GetFieldDefn(i)
    outLayer.CreateField(fieldDefn)

# get the output layer's feature definition
outLayerDefn = outLayer.GetLayerDefn()

# loop through the input features
inFeature = inLayer.GetNextFeature()
while inFeature:
    # get the input geometry
    geom = inFeature.GetGeometryRef()
    # reproject the geometry
    geom.Transform(coordTrans)
    # create a new feature
    outFeature = ogr.Feature(outLayerDefn)
    # set the geometry and attribute
    outFeature.SetGeometry(geom)
    for i in range(0, outLayerDefn.GetFieldCount()):
        outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                            inFeature.GetField(i))
    # add the feature to the shapefile
    outLayer.CreateFeature(outFeature)
    # dereference the features and get the next input feature
    outFeature = None
    inFeature = inLayer.GetNextFeature()

# Save and close the shapefiles
inDataSet = None
outDataSet = None

# ===============================================
# Make raster
# ===============================================
# https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#convert-an-ogr-file-to-a-raster

# Define pixel_size and NoData value of new raster
pixel_size = 1000
NoData_value = 0

# Filename of input OGR file
vector_fn = "continents/africa_aea.shp"

# Filename of the raster Tiff that will be created
raster_fn = "continents/africa.tif"

# Open the data source and read in the extent
source_ds = ogr.Open(vector_fn)
source_layer = source_ds.GetLayer()
x_min, x_max, y_min, y_max = source_layer.GetExtent()

# Create the destination data source
x_res = int(np.ceil((x_max - x_min) / pixel_size))
y_res = int(np.ceil((y_max - y_min) / pixel_size))
target_ds = gdal.GetDriverByName('GTiff').Create(raster_fn, x_res, y_res, 1,
                                                 gdal.GDT_Byte,
                                                 options=["COMPRESS=LZW"])
target_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
target_ds.SetProjection(outSpatialRef.ExportToWkt())
band = target_ds.GetRasterBand(1)
band.SetNoDataValue(NoData_value)

target_ds.GetMetadata()

# Rasterize
gdal.RasterizeLayer(target_ds, [1], source_layer, burn_values=[1])
target_ds = None

# End
