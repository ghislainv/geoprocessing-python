#!/usr/bin/python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from osgeo import gdal, osr
from matplotlib.colors import ListedColormap

# Color map
# comp_dict = dict([[0,['#ffffff','not_suitable']],[1,['#006d2c','HL']],
# [2,['#31a354','ML']],[3,['#bae4b3','LL']],
# [4,['#2b8cbe','HM']],[5,['#a6bddb','MM']],
# [6,['#ece7f2','LM']],[7,['#a50f15','HH']],
# [8,['#de2d26','MH']],[9,['#fcae91','LH']],
# [10,['#ff00ff','PA']]])
# Set transparency for zero (#ffffff00)
colors = ['#ffffff00', '#006d2c', '#31a354', '#bae4b3',
          '#2b8cbe', '#a6bddb', '#ece7f2', '#a50f15',
          '#de2d26', '#fcae91', '#ff00ff']
color_map = ListedColormap(colors)


def convertXY(xy_source, inproj, outproj):
    # function to convert coordinates

    shape = xy_source[0, :, :].shape
    size = xy_source[0, :, :].size

    # the ct object takes and returns pairs of x,y, not 2d grids
    # so the the grid needs to be reshaped (flattened) and back.
    ct = osr.CoordinateTransformation(inproj, outproj)
    xy_target = np.array(ct.TransformPoints(xy_source.reshape(2, size).T))

    xx = xy_target[:, 0].reshape(shape)
    yy = xy_target[:, 1].reshape(shape)

    return xx, yy

# Read the data and metadata
ds = gdal.Open("areas_of_compromise.tif")
gt = ds.GetGeoTransform()
proj = ds.GetProjection()
band = ds.GetRasterBand(1)

# Build overview at 5km
if band.GetOverviewCount() == 0:
    ds.BuildOverviews("nearest", [5])

# Get overview
data = band.GetOverview(0).ReadAsArray()

# Get the coordinates of the center of the pixels
xres = 5000
yres = -5000
xmin = gt[0] + xres * 0.5
xmax = gt[0] + (xres * data.shape[1]) - xres * 0.5
ymin = gt[3] + (yres * data.shape[0]) - yres * 0.5
ymax = gt[3] + yres * 0.5

# Dereference raster
ds = None

# Create a grid of xy coordinates in the original projection
xy_source = np.mgrid[xmin:xmax + xres:xres, ymax:ymin + yres:yres]

# Create the projection objects for the convertion
in_proj = osr.SpatialReference()
in_proj.ImportFromWkt(proj)
out_proj = osr.SpatialReference()
out_proj.ImportFromEPSG(4326)
# Convert to latlong
xx, yy = convertXY(xy_source, in_proj, out_proj)

# Setup basemap
plt.rcParams['hatch.linewidth'] = 0.001
m = Basemap(resolution='l', area_thresh=100000., projection='cyl',
            llcrnrlat=-28, llcrnrlon=-20, urcrnrlat=13, urcrnrlon=52)
m.drawcoastlines(linewidth=0.1)
m.drawcountries(linewidth=0.3, color='white')
m.fillcontinents(color='darkgrey', lake_color='darkgrey',
                 zorder=0)  # zorder=0 to paint over continents

# Plot the data
xx_m, yy_m = m(xx, yy)  # Convert latlong coordinates to basemap proj
im = m.pcolormesh(xx_m, yy_m, data.T, cmap=color_map)

plt.title("Areas of compromise")
plt.savefig("areas_of_compromise.png", dpi=300)

# End
