import warnings

import numpy as np
import pyqtgraph as pg

from AnyQt import QtCore


from orangecontrib.b22.visuals.components.curveplot.utils import NAN




class PlotCurvesItem(pg.GraphicsObject):
    """ Multiple curves on a single plot that can be cached together. """

    def __init__(self):
        pg.GraphicsObject.__init__(self)
        self.clear()


    def clear(self):
        self.bounds = [NAN, NAN, NAN, NAN]
        self.default_bounds = 0, 0, 1, 1
        self.objs = []


    def paint(self, p, *args):
        for o in sorted(self.objs, key=lambda x: x.zValue()):
            o.paint(p, *args)


    def add_bounds(self, c):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # NaN warnings are expected
            try:
                cb = c.boundingRect()
            except ValueError:  # workaround for pyqtgraph 0.10 when there are infs
                cb = QtCore.QRectF()
            # keep undefined elements NaN
            self.bounds[0] = np.nanmin([cb.left(), self.bounds[0]])
            self.bounds[1] = np.nanmin([cb.top(), self.bounds[1]])
            self.bounds[2] = np.nanmax([cb.right(), self.bounds[2]])
            self.bounds[3] = np.nanmax([cb.bottom(), self.bounds[3]])


    def add_curve(self, c, ignore_bounds=False):
        if not ignore_bounds:
            self.add_bounds(c)
        self.objs.append(c)


    def boundingRect(self):
        # replace undefined (NaN) elements with defaults
        bounds = [d if np.isnan(b) else b for b, d in zip(self.bounds, self.default_bounds)]
        return QtCore.QRectF(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
