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
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
# import os


def color_map(plot_type="prob"):
    if (plot_type == "prob"):
        # Colormap
        colors = []
        cmax = 255.0  # float for division
        vmax = 65535.0  # float for division
        colors.append((0, (0, 0, 0, 0)))  # transparent
        colors.append((1 / vmax, (34 / cmax, 139 / cmax, 34 / cmax, 1)))
        colors.append((45000 / vmax, (1, 165 / cmax, 0, 1)))  # orange
        colors.append((55000 / vmax, (1, 0, 0, 1)))  # red
        colors.append((1, (0, 0, 0, 1)))  # black
        color_map = LinearSegmentedColormap.from_list(name="mycm",
                                                      colors=colors,
                                                      N=65535, gamma=1.0)
    elif (plot_type == "fcc"):
        # Colormap
        colors = []
        cmax = 255.0  # float for division
        col_defor = (227, 26, 28, 255)
        col_defor = tuple(np.array(col_defor) / cmax)
        colors.append(col_defor)  # default is red
        colors.append((51 / cmax, 160 / cmax, 44 / cmax, 1))  # forest green
        colors.append((0, 0, 0, 0))  # transparent
        color_map = ListedColormap(colors)
    elif (plot_type == "forest"):
        # Colormap
        colors = []
        cmax = 255.0  # float for division
        colors.append((51 / cmax, 160 / cmax, 44 / cmax, 1))  # forest green
        colors.append((0, 0, 0, 0))  # transparent
        color_map = ListedColormap(colors)
    return(color_map)


# Coordinate conversion
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

# Build overview
if band.GetOverviewCount() == 0:
    ds.BuildOverviews("nearest", [5])

# Get overview
data = band.GetOverview(0).ReadAsArray()

# get the edge coordinates and add half the resolution
# to go to center coordinates
xres = 5000
yres = -5000
xmin = gt[0] + xres * 0.5
xmax = gt[0] + (xres * data.shape[1]) - xres * 0.5
ymin = gt[3] + (yres * data.shape[0]) - yres * 0.5
ymax = gt[3] + yres * 0.5

ds = None

# create a grid of xy coordinates in the original projection
xy_source = np.mgrid[xmin:xmax + xres:xres, ymax - yres:ymin:yres]

# Create the projection objects for the convertion
inproj = osr.SpatialReference()
inproj.ImportFromWkt(proj)
# Get the target projection from the basemap object
outproj = osr.SpatialReference()
proj_merc = "+lon_0=20 +lat_ts=20.0 +R=6370997.0 +proj=merc \
+x_0=-0.0 +units=m +y_0=4567371.38315"
outproj.ImportFromProj4(proj_merc)

# Convert from source projection to basemap projection
xx, yy = convertXY(xy_source, inproj, outproj)

# Create the figure and basemap object
fig = plt.figure()
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
# setup mercator map projection.
m = Basemap(llcrnrlon=-20., llcrnrlat=-40., urcrnrlon=60., urcrnrlat=40.,
            resolution="l", projection="merc")

# plot the data
im1 = m.pcolormesh(xx, yy, data.T, cmap=plt.cm.jet)

# Draw country
m.drawcoastlines()
m.drawcountries()
# draw parallels
m.drawparallels(np.arange(-40, 40, 20), labels=[1, 1, 0, 1])
# draw meridians
m.drawmeridians(np.arange(-20, 60, 20), labels=[1, 1, 0, 1])

# Title
ax.set_title("Areas of compromise")

# Save plot
plt.savefig("areas_of_compromise.png", dpi=150)

# End
