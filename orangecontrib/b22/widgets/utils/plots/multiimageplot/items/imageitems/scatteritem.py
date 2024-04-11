import numpy as np

from AnyQt import QtWidgets, QtCore, QtGui

import pyqtgraph as pg

from scipy import spatial

from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItem




class ScatterItem(ImageItem, pg.ScatterPlotItem):
    id = "Scatter"

    
    def __init__(self, *args, **kwargs):
        ImageItem.__init__(self, *args, **kwargs)
        pg.ScatterPlotItem.__init__(self, *args, **kwargs)

        self.default_pxmode = False # Absolute
        self.default_rel_size = 2
        self.default_abs_size = 1

        self.levels = None
        self.lookup_table = None


    def refresh(self):
        self.set_data(self.imdata, self.domain, self.coords, self.image_values_fixed_levels)

    
    def setLevels(self, levels):
        self.levels = levels
        self.refresh()

    
    def setLookupTable(self, lookup_table):
        self.lookup_table = lookup_table
        self.refresh()


    def calculate_values(self, imdata):
        imdata = imdata.reshape((-1, imdata.shape[-1]), order="f")

        if self.levels is not None:
            if isinstance(self.levels[0], (int | float)):
                lower, upper = self.levels
            
            else:
                lower, upper = list(zip(*self.levels))
            
            imdata = np.clip(imdata, lower, upper)

        lower = np.nanmin(imdata, axis=0)
        upper = np.nanmax(imdata, axis=0)

        diff = upper - lower

        imdata[:, diff==0] = 0
        imdata[:, diff!=0] = (255 * (imdata[:, diff!=0] - lower[diff!=0]) / diff[diff!=0])

        imdata = imdata.astype(int)

        if self.lookup_table is not None and imdata.shape[1] == 1:
            index = imdata.flatten()

            imdata = self.lookup_table[index].astype(int)

        if imdata.shape[1] == 1:
            return [QtGui.QColor(row[0], row[0], row[0]) for row in imdata]
    
        elif imdata.shape[1] == 3:
            return [QtGui.QColor(*list(row)) for row in imdata]
        
        else:
            raise ValueError("ERROR!")


    def get_brushes(self, data):
        imdata = self.get_values(data)

        levels = (np.nanmin(imdata), np.nanmax(imdata))

        leveled = 255 * (imdata - levels[0]) / (levels[1] - levels[0])

        return leveled.reshape((-1, imdata.shape[-1]))


    def set_data(self, imdata, domain, coords, image_values_fixed_levels):
        ImageItem.set_data(self, imdata, domain, coords, image_values_fixed_levels)

        brushes = self.calculate_values(imdata)
        
        pg.ScatterPlotItem.setData(self, pos=coords, brush=brushes)

        tree = spatial.cKDTree(coords)

        # Remove (by setting to infinity) all distances of 0 so that
        # the any points closest coordinate ISN'T itself.
        _, indices = tree.query(coords, k=2)

        # Get the index of the smallest distance for all coordinates
        # and get said closest coordinate's value.
        closest = coords[indices[:, 1], :]

        # Find the median of the absolute step size.
        diffs = np.sort(np.abs(coords - closest), axis=1)

        steps = np.median(diffs, axis=0)

        d = np.sqrt(np.sum(np.square(steps)))
        k = d * 0.7

        self.default_abs_size = round(k, 2)

    
    def set_border(self, pen):
        raise NotImplementedError()


    def add_menu(self, menu):
        self.pxmode = QtWidgets.QAction("Relative Size", menu, checkable=True)
        self.pxmode.toggled.connect(self.change_values)
        menu.addAction(self.pxmode)

        box = QtWidgets.QWidgetAction(self)

        self.scale = QtWidgets.QLineEdit()
        validator = QtGui.QDoubleValidator(0, 99.99, 2)

        self.scale.setValidator(validator)
        self.scale.textChanged.connect(self.change_values)

        box.setDefaultWidget(self.scale)
        menu.addAction(box)

        self.set_defaults()
        self.change_values()


    def set_defaults(self):
        self.pxmode.setChecked(self.default_pxmode)

        if self.default_pxmode:
            default_size = self.default_rel_size
        
        else:
            default_size = self.default_abs_size

        self.scale.setText(str(default_size))

    
    def change_values(self):
        pxmode = self.pxmode.isChecked()
        scale = self.scale.text()
        if scale == "":
            scale = 0

        self.setPxMode(pxmode)
        self.setSize(float(scale))
