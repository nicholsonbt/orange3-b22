import numpy as np

from AnyQt import QtCore, QtGui, QtWidgets

import pyqtgraph as pg

import Orange.data

from Orange.widgets import gui, widget, settings

from Orange.widgets.visualize.utils import plotutils

from Orange.widgets.utils.itemmodels import DomainModel, PyListModel

from orangecontrib.spectroscopy.widgets.owspectra import CurvePlot

from orangecontrib.b22.widgets.utils.editors.hypereditor import HyperEditor

from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import SettingsHandlerMixin

from AnyQt.QtCore import pyqtSignal


def reconnect(signal, handler):
    try:
        signal.disconnect()
    except TypeError:
        pass

    signal.connect(handler)



class MultiSpectra(QtWidgets.QWidget, widget.OWComponent, SettingsHandlerMixin):
    updated = pyqtSignal(int, bool)

    hypereditor = settings.SettingProvider(HyperEditor)


    def __init__(self, parent, **kwargs):
        QtWidgets.QWidget.__init__(self)
        widget.OWComponent.__init__(self, parent)
        SettingsHandlerMixin.__init__(self)

        self.parent = parent

        self.parent.datas_set.connect(self.datas_set)
        self.parent.datas_removed.connect(self.datas_removed)
        self.parent.datas_inserted.connect(self.datas_inserted)

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setMovable(True)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.tab_widget)


    def _index(self, index):
        return self.tab_widget.widget(index)


    def datas_set(self):
        self.tab_widget.clear()

        for _ in self.parent.datas:
            tab = HyperEditor()
            self.tab_widget.addTab(tab, "ERROR!")

        self.refresh_tabs()


    def datas_removed(self, index):
        self.tab_widget.removeTab(index)

        self.refresh_tabs()


    def datas_inserted(self, index):
        print(f"Inserted 2: {index}")
        tab = HyperEditor()
        self.tab_widget.insertTab(index, tab, "ERROR!")

        self.refresh_tabs()

        self.updated.emit(index, True)


    def refresh_tabs(self):
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabText(i, f"Table {i}")
            tab = self._index(i)
            tab.set_data(self.parent.datas[i].table)
            reconnect(tab.updated, lambda flag, i=i: (self.updated.emit(i, flag), print("Redrawing data 2")))
        

    def image_values(self, index):
        print(index, self.tab_widget.count())
        return self._index(index).image_values()
    

    def image_values_fixed_levels(self, index):
        return self._index(index).image_values_fixed_levels()
    
