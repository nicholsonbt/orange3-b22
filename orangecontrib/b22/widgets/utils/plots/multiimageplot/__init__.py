import numpy as np

from AnyQt import QtCore, QtGui, QtWidgets

import pyqtgraph as pg

import Orange.data

from Orange.widgets import gui, widget, settings

from Orange.widgets.visualize.utils import plotutils

from Orange.widgets.utils.itemmodels import DomainModel, PyListModel

from orangecontrib.spectroscopy.widgets.owspectra import InteractiveViewBox, \
    MenuFocus, CurvePlot, SELECTONE, SELECTMANY, INDIVIDUAL

from orangecontrib.b22.widgets.utils.plots.multiimageplot.multiplotlayout import MultiPlotLayout

from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import SettingsHandlerMixin


class MultiPlot(QtWidgets.QWidget, widget.OWComponent, SettingsHandlerMixin):
    # The x and y axes of the plots (must be the same across all input
    # tables).
    attr_x = settings.ContextSetting(None, exclude_attributes=True)
    attr_y = settings.ContextSetting(None, exclude_attributes=True)

    plot = settings.SettingProvider(MultiPlotLayout)

    # Selected plot changed.
    highlighted_changed = QtCore.pyqtSignal()

    # Selection of pixels within the plots changed.
    selection_changed = QtCore.pyqtSignal()

    # Input data changed.
    image_updated = QtCore.pyqtSignal()

    datas_set = QtCore.pyqtSignal()
    datas_removed = QtCore.pyqtSignal(int)
    datas_inserted = QtCore.pyqtSignal(int)

    # The index and if the image_values has changed.
    multispectra_updated = QtCore.pyqtSignal(int, bool)


    def __init__(self, parent, **kwargs):
        QtWidgets.QWidget.__init__(self)
        widget.OWComponent.__init__(self, parent)
        SettingsHandlerMixin.__init__(self)

        self.parent = parent

        self.parent.multispectra_updated.connect(self.multispectra_updated.emit)
        self.parent.datas_set.connect(self._datas_set)
        self.parent.datas_removed.connect(self._datas_removed)
        self.parent.datas_inserted.connect(self._datas_inserted)

        self.selection_type = kwargs.get("selection_type", SELECTMANY)
        self.saving_enabled = kwargs.get("saving_enabled", True)
        self.selection_enabled = kwargs.get("selection_enabled", True)
        self.viewtype = kwargs.get("viewtype", INDIVIDUAL)

        self.selection_groups = []
        self.highlighted_plot = None

        self.plot = MultiPlotLayout(self)

        self.plotview = plotutils.GraphicsView()
        self.plotview.setCentralItem(self.plot)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.plotview)

        layout = QtWidgets.QGridLayout()
        self.plotview.setLayout(layout)
        self.button = QtWidgets.QPushButton("Menu", self.plotview)
        self.button.setAutoDefault(False)

        layout.setRowStretch(1, 1)
        layout.setColumnStretch(1, 1)
        layout.addWidget(self.button, 0, 0)
        view_menu = MenuFocus(self)
        self.button.setMenu(view_menu)

        self.add_choose_xy(view_menu)
        self.add_zoom_actions(view_menu)


    def add_zoom_actions(self, menu):
        zoom_in = QtWidgets.QAction(
            "Zoom in", self, triggered=self.plot.images.set_mode_zooming
        )

        zoom_in.setShortcuts([QtCore.Qt.Key_Z, QtGui.QKeySequence(QtGui.QKeySequence.ZoomIn)])
        zoom_in.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.addAction(zoom_in)

        if menu:
            menu.addAction(zoom_in)

        zoom_fit = QtWidgets.QAction(
            "Zoom to fit", self,
            triggered=lambda x: (self.plot.images.autoRange(), self.plot.images.set_mode_panning())
        )

        zoom_fit.setShortcuts([QtCore.Qt.Key_Backspace, QtGui.QKeySequence(QtCore.Qt.ControlModifier | QtCore.Qt.Key_0)])
        zoom_fit.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.addAction(zoom_fit)

        if menu:
            menu.addAction(zoom_fit)


    def add_choose_xy(self, menu):
        common_options = dict(
            labelWidth=50, orientation=QtCore.Qt.Horizontal, sendSelectedValue=True
        )

        choose_xy = QtWidgets.QWidgetAction(self)
        box = gui.vBox(self)
        box.setContentsMargins(10, 0, 10, 0)
        box.setFocusPolicy(QtCore.Qt.TabFocus)
        self.xy_model = PyListModel()

        self.cb_attr_x = gui.comboBox(
            box, self, "attr_x", label="Axis x:", callback=self.attrs_changed,
            model=self.xy_model, **common_options
        )

        self.cb_attr_y = gui.comboBox(
            box, self, "attr_y", label="Axis y:", callback=self.attrs_changed,
            model=self.xy_model, **common_options
        )

        box.setFocusProxy(self.cb_attr_x)

        choose_xy.setDefaultWidget(box)
        menu.addAction(choose_xy)


    def _datas_set(self):
        if not self.init_attr_values():
            self.datas_set.emit()


    def _datas_removed(self, index):
        if not self.init_attr_values():
            self.datas_removed.emit(index)


    def _datas_inserted(self, index):
        if not self.init_attr_values():
            self.datas_inserted.emit(index)


    def attrs_changed(self):
        self.datas_set.emit()
        

    def init_attr_values(self):
        valid = []

        tables = [data.table for data in self.parent.datas if data is not None]
        models = [self.new_domain_model(table) for table in tables if table is not None]

        if len(models) > 0:
            valid = list(models[0])

            for model in models[1:]:
                i = 0

                while i < len(valid):
                    attr_0 = valid[i]

                    flag = False

                    for attr_1 in model:
                        if attr_0 == attr_1:
                            flag = True
                            break
                    
                    if flag:
                        i += 1

                    else:
                        valid.pop(i)

        self.xy_model.clear()
        self.xy_model.extend([attr.name for attr in valid])

        old_attr_x = self.attr_x
        old_attr_y = self.attr_y

        self.attr_x = self.xy_model[0] if self.xy_model else None
        self.attr_y = self.xy_model[1] if len(self.xy_model) >= 2 else self.attr_x

        if old_attr_x != self.attr_x or old_attr_y != self.attr_y:
            self.attrs_changed()
            return True
        
        return False


    def new_domain_model(self, data):
        model = DomainModel(DomainModel.METAS | DomainModel.CLASSES,
                            valid_types=DomainModel.PRIMITIVE)
        
        model.set_domain(data.domain)

        return model
    

    def image_values(self, index):
        return self.parent.image_values(index)
    
    def image_values_fixed_levels(self, index):
        return self.parent.image_values_fixed_levels(index)

    