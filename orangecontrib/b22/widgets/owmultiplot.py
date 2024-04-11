import numpy as np

from AnyQt import QtCore, QtGui, QtWidgets

import pyqtgraph as pg

import Orange.data

from Orange.widgets import gui, widget, settings

from orangecontrib.b22.widgets.utils.hypertable import Hypertable
from orangecontrib.b22.widgets.utils.plots.multiimageplot import MultiPlot
from orangecontrib.b22.widgets.utils.plots.multispectraplot import MultiSpectra


from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import SettingsHandlerMixin



class OWMultiPlot(widget.OWWidget, SettingsHandlerMixin):
    name = "MultiPlot"

    class Inputs:
        datas = widget.MultiInput("Data", Orange.data.Table, default=True)

    class Outputs():
        pass

    imageplot = settings.SettingProvider(MultiPlot)
    multispectra = settings.SettingProvider(MultiSpectra)


    attrs = settings.Setting(["map_x", "map_y"])

    datas_set = QtCore.pyqtSignal()
    datas_removed = QtCore.pyqtSignal(int)
    datas_inserted = QtCore.pyqtSignal(int)

    multispectra_updated = QtCore.pyqtSignal(int, bool)


    def __init__(self):
        widget.OWWidget.__init__(self)
        SettingsHandlerMixin.__init__(settings.DomainContextHandler)

        self.datas = []

        splitter = QtWidgets.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)

        self.imageplot = MultiPlot(self)
        self.multispectra = MultiSpectra(self)
        self.multispectra.updated.connect(self.multispectra_updated.emit)

        splitter.addWidget(self.imageplot)
        splitter.addWidget(self.multispectra)

        splitter.setSizes([100,100])

        self.mainArea.layout().addWidget(splitter)
        self.resize(900, 700)


    @Inputs.datas
    def set_datas(self, datas):
        self.datas = [Hypertable.from_table(data, self.attrs) for data in datas]
        self.datas_set.emit()


    @Inputs.datas.insert
    def insert_data(self, index, data):
        print(f"Insert: {index}")
        self.datas.insert(index, Hypertable.from_table(data, self.attrs))
        self.datas_inserted.emit(index)


    @Inputs.datas.remove
    def remove_data(self, index):
        self.datas.pop(index)
        self.datas_removed.emit(index)
    

    def onDeleteWidget(self):
        # self.curveplot.shutdown()
        # self.imageplot.shutdown()
        super().onDeleteWidget()

    
    def image_values(self, index):
        return self.multispectra.image_values(index)
    
    def image_values_fixed_levels(self, index):
        return self.multispectra.image_values_fixed_levels(index)








if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWMultiPlot).run(set_data=collagen)