import numpy as np

from AnyQt import QtCore, QtWidgets

from orangecontrib.spectroscopy.widgets.line_geometry import distance_curves




SELECT_SQUARE = 123
SELECT_POLYGON = 124

# view types
INDIVIDUAL = 0
AVERAGE = 1

# selections
SELECTNONE = 0
# SELECTONE = 1
SELECTMANY = 2

MAX_INSTANCES_DRAWN = 1000
MAX_THICK_SELECTED = 10
NAN = float("nan")

# distance to the first point in pixels that finishes the polygon
SELECT_POLYGON_TOLERANCE = 10

COLORBREWER_SET1 = [(228, 26, 28), (55, 126, 184), (77, 175, 74), (152, 78, 163), (255, 127, 0),
                    (255, 255, 51), (166, 86, 40), (247, 129, 191), (153, 153, 153)]


def selection_modifiers():
    keys = QtWidgets.QApplication.keyboardModifiers()
    add_to_group = bool(keys & QtCore.Qt.ControlModifier)
    add_group = bool(keys & QtCore.Qt.ShiftModifier)
    remove = bool(keys & QtCore.Qt.AltModifier)
    return add_to_group, add_group, remove


def closestindex(array, v, side="left"):
    """
    Return index of a 1d sorted array closest to value v.
    """
    fi = np.searchsorted(array, v, side=side)
    if fi == 0:
        return 0
    elif fi == len(array):
        return len(array) - 1
    else:
        return fi - 1 if v - array[fi - 1] < array[fi] - v else fi


def distancetocurves(array, x, y, xpixel, ypixel, r=5, cache=None):
    # xpixel, ypixel are sizes of pixels
    # r how many pixels do we look around
    # array - curves in both x and y
    # x,y position in curve coordinates
    if cache is not None and id(x) in cache:
        xmin, xmax = cache[id(x)]
    else:
        xmin = closestindex(array[0], x - r * xpixel)
        xmax = closestindex(array[0], x + r * xpixel, side="right")
        if cache is not None:
            cache[id(x)] = xmin, xmax
    xmin = max(0, xmin - 1)
    xp = array[0][xmin:xmax + 2]
    yp = array[1][:, xmin:xmax + 2]

    # convert to distances in pixels
    xp = (xp - x) / xpixel
    yp = (yp - y) / ypixel

    # add edge point so that distance_curves works if there is just one point
    xp = np.hstack((xp, float("nan")))
    yp = np.hstack((yp, np.zeros((yp.shape[0], 1)) * float("nan")))
    dc = distance_curves(xp, yp, (0, 0))
    return dc
