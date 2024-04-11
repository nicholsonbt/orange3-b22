import pyqtgraph as pg

from AnyQt import QtCore, QtGui


class SelectRegion(pg.LinearRegionItem):
    def __init__(self, *args, **kwargs):
        pg.LinearRegionItem.__init__(self, *args, **kwargs)
        for l in self.lines:
            l.setCursor(QtCore.Qt.SizeHorCursor)
        self.setZValue(10)
        color = QtGui.QColor(QtCore.Qt.red)
        color.setAlphaF(0.05)
        self.setBrush(pg.mkBrush(color))