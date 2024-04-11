import itertools
from collections import defaultdict
import random
from xml.sax.saxutils import escape
import bottleneck
import numpy as np
import pyqtgraph as pg

from AnyQt import QtCore, QtGui, QtWidgets



from Orange.data import DiscreteVariable
from Orange.widgets.widget import OWWidget, OWComponent
from Orange.widgets import gui
from Orange.widgets.settings import Setting, ContextSetting
from Orange.widgets.utils.itemmodels import DomainModel
from Orange.widgets.utils.plot import ZOOMING
from Orange.widgets.utils import saveplot
from Orange.widgets.visualize.owscatterplotgraph import LegendItem
from Orange.widgets.visualize.utils.plotutils import HelpEventDelegate, PlotWidget

from orangecontrib.spectroscopy.data import getx
from orangecontrib.spectroscopy.widgets.line_geometry import intersect_curves_chunked
from orangecontrib.spectroscopy.widgets.gui import pixel_decimals, \
    VerticalPeakLine, float_to_str_decimals as strdec
from orangecontrib.spectroscopy.widgets.utils import SelectionGroupMixin


from orangecontrib.b22.visuals.components.curveplot.parametersetter import ParameterSetter
from orangecontrib.b22.visuals.components.curveplot.finiteplotcurveitem import FinitePlotCurveItem
from orangecontrib.b22.visuals.components.curveplot.plotcurvesitem import PlotCurvesItem
from orangecontrib.b22.visuals.components.curveplot.showaverage import ShowAverage
from orangecontrib.b22.visuals.components.curveplot.showindividual import ShowIndividual
from orangecontrib.b22.visuals.components.curveplot.interactiveviewboxc import InteractiveViewBoxC
from orangecontrib.b22.visuals.components.curveplot.menufocus import MenuFocus
from orangecontrib.b22.visuals.components.curveplot.nosuchcurve import NoSuchCurve
from orangecontrib.b22.visuals.components.curveplot.utils import INDIVIDUAL, AVERAGE, \
    SELECTNONE, SELECTMANY, MAX_INSTANCES_DRAWN, MAX_THICK_SELECTED, COLORBREWER_SET1, \
    selection_modifiers, closestindex, distancetocurves


from orangecontrib.b22.visuals.components.curveplot.mixins import PerspectiveMixin

from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import SettingsHandlerMixin


class CurvePlot(QtWidgets.QWidget, OWComponent, SettingsHandlerMixin, SelectionGroupMixin, PerspectiveMixin):

    sample_seed = Setting(0, schema_only=True)
    peak_labels_saved = Setting([], schema_only=True)
    feature_color = ContextSetting(None, exclude_attributes=True)
    color_individual = Setting(False)  # color individual curves (in a cycle) if no feature_color
    invertX = Setting(False)
    viewtype = Setting(INDIVIDUAL)
    show_grid = Setting(False)

    selection_changed = QtCore.pyqtSignal()
    new_sampling = QtCore.pyqtSignal(object)
    highlight_changed = QtCore.pyqtSignal()
    locked_axes_changed = QtCore.pyqtSignal(bool)
    graph_shown = QtCore.pyqtSignal()

    def __init__(self, parent: OWWidget, select=SELECTNONE):
        QtWidgets.QWidget.__init__(self)
        OWComponent.__init__(self, parent)
        SettingsHandlerMixin.__init__(self)
        SelectionGroupMixin.__init__(self)

        self.parent = parent
        
        PerspectiveMixin.__init__(self)

        self.show_average_thread = ShowAverage(self)
        self.show_average_thread.shown.connect(self.rescale)
        self.show_average_thread.shown.connect(self.graph_shown.emit)

        self.show_individual_thread = ShowIndividual(self)
        self.show_individual_thread.shown.connect(self.rescale)
        self.show_individual_thread.shown.connect(self.graph_shown.emit)

        

        self.selection_type = select
        self.select_at_least_1 = False
        self.saving_enabled = True
        self.clear_data()
        self.subset = None  # current subset input, an array of indices
        self.subset_indices = None  # boolean index array with indices in self.data

        self.plotview = PlotWidget(viewBox=InteractiveViewBoxC(self))
        self.plot = self.plotview.getPlotItem()
        self.plot.hideButtons()  # hide the autorange button
        self.plot.setDownsampling(auto=True, mode="peak")

        self.connected_views = []
        self.plot.vb.sigResized.connect(self._update_connected_views)

        for pos in ["top", "right"]:
            self.plot.showAxis(pos, True)
            self.plot.getAxis(pos).setStyle(showValues=False)

        self.markings = []
        self.peak_labels = []

        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plot.scene().sigMouseMoved.connect(self.mouse_moved_viewhelpers)
        self.plot.scene().sigMouseMoved.connect(self.plot.vb.mouseMovedEvent)
        self.proxy = pg.SignalProxy(self.plot.scene().sigMouseMoved, rateLimit=20,
                                    slot=self.mouse_moved_closest, delay=0.1)
        self.plot.vb.sigRangeChanged.connect(self.resized)
        self.plot.vb.sigResized.connect(self.resized)
        self.pen_mouse = pg.mkPen(color=(0, 0, 255), width=2)
        pen_normal, pen_selected, pen_subset = self._generate_pens(QtGui.QColor(60, 60, 60, 200),
                                                                   QtGui.QColor(200, 200, 200, 127),
                                                                   QtGui.QColor(0, 0, 0, 255))
        self._default_pen_selected = pen_selected
        self.pen_normal = defaultdict(lambda: pen_normal)
        self.pen_subset = defaultdict(lambda: pen_subset)
        self.pen_selected = defaultdict(lambda: pen_selected)

        self.label = pg.TextItem("", anchor=(1, 0), fill="#FFFFFFBB")
        self.label.setText("", color=(0, 0, 0))
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.label.setFont(font)
        self.label.setZValue(100000)

        self.discrete_palette = None
        QtGui.QPixmapCache.setCacheLimit(max(QtGui.QPixmapCache.cacheLimit(), 100 * 1024))
        self.curves_cont = PlotCurvesItem()
        self.important_decimals = 10, 10

        self.plot.scene().installEventFilter(
            HelpEventDelegate(self.help_event, self))

        # whether to rescale at next update
        self.rescale_next = True

        self.MOUSE_RADIUS = 20

        self.clear_graph()

        self.load_peak_labels()

        # interface settings
        self.location = True  # show current position
        self.markclosest = True  # mark
        self.crosshair = True
        self.crosshair_hidden = True

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.plotview)

        # prepare interface according to the new context
        self.parent.contextAboutToBeOpened.connect(lambda x: self.init_interface_data(x[0]))

        actions = []

        resample_curves = QtWidgets.QAction(
            "Resample curves", self, shortcut=QtCore.Qt.Key_R,
            triggered=lambda x: self.resample_curves(self.sample_seed+1)
        )
        resample_curves.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(resample_curves)
        reset_curves = QtWidgets.QAction(
            "Resampling reset", self, shortcut=QtGui.QKeySequence(QtCore.Qt.ControlModifier | QtCore.Qt.Key_R),
            triggered=lambda x: self.resample_curves(0)
        )
        reset_curves.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(reset_curves)

        zoom_in = QtWidgets.QAction(
            "Zoom in", self, triggered=self.plot.vb.set_mode_zooming
        )
        zoom_in.setShortcuts([QtCore.Qt.Key_Z, QtGui.QKeySequence(QtGui.QKeySequence.ZoomIn)])
        zoom_in.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(zoom_in)
        zoom_fit = QtWidgets.QAction(
            "Zoom to fit", self,
            triggered=lambda x: (self.plot.vb.autoRange(), self.plot.vb.set_mode_panning())
        )
        zoom_fit.setShortcuts([QtCore.Qt.Key_Backspace, QtGui.QKeySequence(QtCore.Qt.ControlModifier | QtCore.Qt.Key_0)])
        zoom_fit.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(zoom_fit)
        rescale_y = QtWidgets.QAction(
            "Rescale Y to fit", self, shortcut=QtCore.Qt.Key_D,
            triggered=self.rescale_current_view_y
        )
        rescale_y.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(rescale_y)

        self.view_average_menu = QtWidgets.QAction(
            "Show averages", self, shortcut=QtCore.Qt.Key_A, checkable=True,
            triggered=lambda x: self.viewtype_changed()
        )
        self.view_average_menu.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(self.view_average_menu)

        self.show_grid_a = QtWidgets.QAction(
            "Show grid", self, shortcut=QtCore.Qt.Key_G, checkable=True,
            triggered=self.grid_changed
        )
        self.show_grid_a.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(self.show_grid_a)
        self.invertX_menu = QtWidgets.QAction(
            "Invert X", self, shortcut=QtCore.Qt.Key_X, checkable=True,
            triggered=self.invertX_changed
        )
        self.invertX_menu.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        actions.append(self.invertX_menu)

        single_peak = QtWidgets.QAction(
            "Add Peak Label", self, shortcut=QtCore.Qt.Key_P,
            triggered=self.add_peak_label
        )
        actions.append(single_peak)
        single_peak.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

        if self.selection_type == SELECTMANY:
            select_curves = QtWidgets.QAction(
                "Select (line)", self, triggered=self.line_select_start,
            )
            select_curves.setShortcuts([QtCore.Qt.Key_S])
            select_curves.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            actions.append(select_curves)
        if self.saving_enabled:
            save_graph = QtWidgets.QAction(
                "Save graph", self, triggered=self.save_graph,
            )
            save_graph.setShortcuts([QtGui.QKeySequence(QtCore.Qt.ControlModifier | QtCore.Qt.Key_S)])
            save_graph.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            actions.append(save_graph)

        layout = QtWidgets.QGridLayout()
        self.plotview.setLayout(layout)
        self.button = QtWidgets.QPushButton("Menu", self.plotview)
        self.button.setAutoDefault(False)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(1, 1)
        layout.addWidget(self.button, 0, 0)
        view_menu = MenuFocus(self)
        self.button.setMenu(view_menu)
        view_menu.addActions(actions)
        self.addActions(actions)
        for a in actions:
            a.setShortcutVisibleInContextMenu(True)

        PerspectiveMixin.add_actions(self, view_menu)

        self.color_individual_menu = QtWidgets.QAction(
            "Color individual curves", self, shortcut=QtCore.Qt.Key_I, checkable=True,
            triggered=lambda x: self.color_individual_changed()
        )
        self.color_individual_menu.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.color_individual_menu.setShortcutVisibleInContextMenu(True)
        view_menu.addAction(self.color_individual_menu)
        self.addAction(self.color_individual_menu)

        choose_color_action = QtWidgets.QWidgetAction(self)
        choose_color_box = gui.hBox(self)
        choose_color_box.setFocusPolicy(QtCore.Qt.TabFocus)
        label = gui.label(choose_color_box, self, "Color by")
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.feature_color_model = DomainModel(DomainModel.METAS | DomainModel.CLASSES,
                                               valid_types=(DiscreteVariable,), placeholder="None")
        self.feature_color_combo = gui.comboBox(
            choose_color_box, self, "feature_color",
            callback=self.update_view, model=self.feature_color_model)
        choose_color_box.setFocusProxy(self.feature_color_combo)
        choose_color_action.setDefaultWidget(choose_color_box)
        view_menu.addAction(choose_color_action)

        cycle_colors = QtWidgets.QShortcut(QtCore.Qt.Key_C, self, self.cycle_color_attr, context=QtCore.Qt.WidgetWithChildrenShortcut)

        self.grid_apply()
        self.invertX_apply()
        self.color_individual_apply()
        self._color_individual_cycle = COLORBREWER_SET1
        self.plot.vb.set_mode_panning()

        PerspectiveMixin.setup(self)

        self.reports = {}  # current reports

        self.legend = self._create_legend()
        self.viewhelpers_show()

        self.parameter_setter = ParameterSetter(self)

    def calculate(self, x, ys):
        return PerspectiveMixin.calculate(self, x, ys)

    def update_lock_indicators(self):
        self.locked_axes_changed.emit(self.plot.vb.is_view_locked())

    def _update_connected_views(self):
        for w in self.connected_views:
            w.setGeometry(self.plot.vb.sceneBoundingRect())

    def _create_legend(self):
        legend = LegendItem()
        legend.setParentItem(self.plotview.getViewBox())
        legend.restoreAnchor(((1, 0), (1, 0)))
        return legend

    def init_interface_data(self, data):
        domain = data.domain if data is not None else None
        self.feature_color_model.set_domain(domain)
        self.feature_color = self.feature_color_model[0] if self.feature_color_model else None

    def line_select_start(self):
        if self.viewtype == INDIVIDUAL:
            self.plot.vb.set_mode_select()

    def help_event(self, ev):
        text = ""
        if self.highlighted is not None:
            if self.viewtype == INDIVIDUAL:
                index = self.sampled_indices[self.highlighted]
                variables = self.data.domain.metas + self.data.domain.class_vars
                text += "".join(
                    '{} = {}\n'.format(attr.name, self.data[index, attr])
                    for attr in variables)
            elif self.viewtype == AVERAGE:
                c = self.multiple_curves_info[self.highlighted]
                nc = sum(c[2])
                if c[0] is not None:
                    text += str(c[0]) + " "
                if c[1]:
                    text += "({})".format(c[1])
                if text:
                    text += "\n"
                text += "{} curves".format(nc)
        if text:
            text = text.rstrip()
            text = ('<span style="white-space:pre">{}</span>'
                    .format(escape(text)))
            QtWidgets.QToolTip.showText(ev.screenPos(), text, widget=self.plotview)
            return True
        else:
            return False

    def report(self, reporter, contents):
        self.reports[id(reporter)] = contents

    def report_finished(self, reporter):
        try:
            self.reports.pop(id(reporter))
        except KeyError:
            pass  # ok if it was already removed
        if not self.reports:
            pass

    def cycle_color_attr(self):
        elements = [a for a in self.feature_color_model]
        currentind = elements.index(self.feature_color)
        next = (currentind + 1) % len(self.feature_color_model)
        self.feature_color = elements[next]
        self.update_view()

    def grid_changed(self):
        self.show_grid = not self.show_grid
        self.grid_apply()

    def grid_apply(self):
        self.plot.showGrid(self.show_grid, self.show_grid, alpha=0.3)
        self.show_grid_a.setChecked(self.show_grid)

    def add_peak_label(self, position=None):
        label_line = VerticalPeakLine()
        label_line.setPos(position if position else np.mean(self.plot.viewRange()[0]))
        label_line.sigDeleteRequested.connect(self.delete_label)
        self.peak_labels.append(label_line)
        self.plotview.addItem(label_line, ignore_bounds=True)
        label_line.updateLabel()  # rounding
        return label_line

    def delete_label(self, label):
        self.peak_labels.remove(label)
        self.plotview.removeItem(label)

    def save_peak_labels(self):
        self.peak_labels_saved = [p.save_info() for p in self.peak_labels]

    def load_peak_labels(self):
        for info in self.peak_labels_saved:
            peak_label = self.add_peak_label()
            peak_label.load_info(info)

    def invertX_changed(self):
        self.invertX = not self.invertX
        self.invertX_apply()

    def invertX_apply(self):
        self.plot.vb.invertX(self.invertX)
        self.resized()
        # force redraw of axes (to avoid a pyqtgraph bug)
        vr = self.plot.vb.viewRect()
        self.plot.vb.setRange(xRange=(0, 1), yRange=(0, 1))
        self.plot.vb.setRange(rect=vr)
        self.invertX_menu.setChecked(self.invertX)

    def color_individual_changed(self):
        self.color_individual = not self.color_individual
        self.color_individual_apply()
        self.update_view()

    def color_individual_apply(self):
        self.color_individual_menu.setChecked(self.color_individual)

    def save_graph(self):
        try:
            self.viewhelpers_hide()
            saveplot.save_plot(self.plotview, self.parent.graph_writers)
        finally:
            self.viewhelpers_show()

    def clear_data(self):
        self.data = None
        self.data_x = None  # already sorted x-axis
        self.data_xsind = None  # sorting indices for x-axis
        self.discrete_palette = None

    def clear_graph(self):
        self.show_average_thread.cancel()
        self.show_individual_thread.cancel()
        self.highlighted = None
        # reset caching. if not, it is not cleared when view changing when zoomed
        self.curves_cont.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        self.curves_cont.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        self.plot.vb.disableAutoRange()
        self.curves_cont.clear()
        self.curves_cont.update()
        self.plotview.clear()
        self.multiple_curves_info = []
        self.curves_plotted = []  # currently plotted elements (for rescale)
        self.curves = []  # for finding closest curve
        self.plotview.addItem(self.label, ignoreBounds=True)
        self.highlighted_curve = FinitePlotCurveItem(pen=self.pen_mouse)
        self.highlighted_curve.setZValue(10)
        self.highlighted_curve.hide()
        self.plot.addItem(self.highlighted_curve, ignoreBounds=True)
        self.plot.addItem(self.vLine, ignoreBounds=True)
        self.plot.addItem(self.hLine, ignoreBounds=True)
        self.viewhelpers = True
        self.plot.addItem(self.curves_cont)

        self.sampled_indices = []
        self.sampled_indices_inverse = {}
        self.new_sampling.emit(None)

        for m in self.markings:
            self.plot.addItem(m, ignoreBounds=True)

        for p in self.peak_labels:
            self.plot.addItem(p, ignoreBounds=True)

    def resized(self):
        self.important_decimals = pixel_decimals(self.plot.vb)

        try:
            vr = self.plot.vb.viewRect()
        except:
            return

        if self.invertX:
            self.label.setPos(vr.bottomLeft())
        else:
            self.label.setPos(vr.bottomRight())

    def make_selection(self, data_indices):
        add_to_group, add_group, remove = selection_modifiers()
        invd = self.sampled_indices_inverse
        data_indices_set = set(data_indices if data_indices is not None else set())
        redraw_curve_indices = set()

        def current_selection():
            return set(icurve for idata, icurve in invd.items() if self.selection_group[idata])

        old_sel_ci = current_selection()

        changed = False

        if add_to_group:  # both keys - need to test it before add_group
            selnum = np.max(self.selection_group)
        elif add_group:
            selnum = np.max(self.selection_group) + 1
        elif remove:
            selnum = 0
        else:
            # remove the current selection
            redraw_curve_indices.update(old_sel_ci)
            if np.any(self.selection_group):
                self.selection_group *= 0  # remove
                changed = True
            selnum = 1
        # add new
        if data_indices is not None:
            self.selection_group[data_indices] = selnum
            redraw_curve_indices.update(
                icurve for idata, icurve in invd.items() if idata in data_indices_set)
            changed = True

        fixes = self.make_selection_valid()
        if fixes:
            changed = True
        redraw_curve_indices.update(
            icurve for idata, icurve in invd.items() if idata in fixes)

        new_sel_ci = current_selection()

        # redraw whole selection if it increased or decreased over the threshold
        if len(old_sel_ci) <= MAX_THICK_SELECTED < len(new_sel_ci) or \
           len(old_sel_ci) > MAX_THICK_SELECTED >= len(new_sel_ci):
            redraw_curve_indices.update(old_sel_ci)

        self.set_curve_pens(redraw_curve_indices)
        if changed:
            self.selection_changed_confirm()

    def make_selection_valid(self):
        """ Make the selection valid and return the changed positions. """
        if self.select_at_least_1 and not len(np.flatnonzero(self.selection_group)) \
                and len(self.data) > 0:  # no selection
            self.selection_group[0] = 1
            return set([0])
        return set()

    def selection_changed_confirm(self):
        # reset average view; individual was already handled in make_selection
        if self.viewtype == AVERAGE:
            self.show_average()
        self.prepare_settings_for_saving()
        self.selection_changed.emit()

    def viewhelpers_hide(self):
        self.label.hide()
        self.vLine.hide()
        self.hLine.hide()

    def viewhelpers_show(self):
        self.label.show()
        if self.crosshair and not self.crosshair_hidden:
            self.vLine.show()
            self.hLine.show()
        else:
            self.vLine.hide()
            self.hLine.hide()

    def mouse_moved_viewhelpers(self, pos):
        if self.plot.sceneBoundingRect().contains(pos):
            mousePoint = self.plot.vb.mapSceneToView(pos)
            posx, posy = mousePoint.x(), mousePoint.y()

            labels = []
            for a, vs in sorted(self.reports.items()):
                for v in vs:
                    if isinstance(v, tuple) and len(v) == 2:
                        if v[0] == "x":
                            labels.append(strdec(v[1], self.important_decimals[0]))
                            continue
                    labels.append(str(v))
            labels = " ".join(labels)
            self.crosshair_hidden = bool(labels)

            if self.location and not labels:
                labels = strdec(posx, self.important_decimals[0]) + "  " + \
                         strdec(posy, self.important_decimals[1])
            self.label.setText(labels, color=(0, 0, 0))

            self.vLine.setPos(posx)
            self.hLine.setPos(posy)
            self.viewhelpers_show()
        else:
            self.viewhelpers_hide()

    def mouse_moved_closest(self, evt):
        pos = evt[0]
        if self.plot.sceneBoundingRect().contains(pos) and \
                self.curves and len(self.curves[0][0]):  # need non-zero x axis!
            mousePoint = self.plot.vb.mapSceneToView(pos)
            posx, posy = mousePoint.x(), mousePoint.y()

            cache = {}
            bd = None
            if self.markclosest and self.plot.vb.action != ZOOMING:
                xpixel, ypixel = self.plot.vb.viewPixelSize()
                distances = distancetocurves(self.curves[0], posx, posy, xpixel, ypixel,
                                             r=self.MOUSE_RADIUS, cache=cache)
                try:
                    mindi = np.nanargmin(distances)
                    if distances[mindi] < self.MOUSE_RADIUS:
                        bd = mindi
                except ValueError:  # if all distances are NaN
                    pass
            if self.highlighted != bd:
                QtWidgets.QToolTip.hideText()
            self.highlight(bd)

    def highlight(self, index, emit=True):
        """
        Highlight shown curve with the given index (of the sampled curves).
        """
        old = self.highlighted
        if index is not None and not 0 <= index < len(self.curves[0][1]):
            raise NoSuchCurve()

        self.highlighted = index
        if self.highlighted is None:
            self.highlighted_curve.hide()
        else:
            if old != self.highlighted:
                x = self.curves[0][0]
                y = self.curves[0][1][self.highlighted]
                self.highlighted_curve.setData(x=x, y=y)
            self.highlighted_curve.show()
        if emit and old != self.highlighted:
            self.highlight_changed.emit()

    def highlighted_index_in_data(self):
        if self.highlighted is not None and self.viewtype == INDIVIDUAL:
            return self.sampled_indices[self.highlighted]
        return None

    def highlight_index_in_data(self, index, emit):
        if self.viewtype == AVERAGE:  # do not highlight average view
            index = None
        if index in self.sampled_indices_inverse:
            index = self.sampled_indices_inverse[index]
        self.highlight(index, emit)

    def _set_selection_pen_width(self):
        n_selected = np.count_nonzero(self.selection_group[self.sampled_indices])
        use_thick = n_selected <= MAX_THICK_SELECTED
        for v in itertools.chain(self.pen_selected.values(), [self._default_pen_selected]):
            v.setWidth(2 if use_thick else 1)

    def set_curve_pen(self, idc):
        idcdata = self.sampled_indices[idc]
        insubset = self.subset_indices[idcdata]
        inselected = self.selection_type and self.selection_group[idcdata]
        have_subset = np.any(self.subset_indices)
        thispen = self.pen_subset if insubset or not have_subset else self.pen_normal
        if inselected:
            thispen = self.pen_selected
        color_var = self.feature_color
        value = None
        if color_var is not None:
            value = str(self.data[idcdata][color_var])
        elif self.color_individual:
            value = idc % len(self._color_individual_cycle)
        self.curves_cont.objs[idc].setPen(thispen[value])
        # to always draw selected above subset, multiply with 2
        self.curves_cont.objs[idc].setZValue(int(insubset) + 2*int(inselected))

    def set_curve_pens(self, curves=None):
        if self.viewtype == INDIVIDUAL and self.curves:
            self._set_selection_pen_width()
            curves = range(len(self.curves[0][1])) if curves is None else curves
            for i in curves:
                self.set_curve_pen(i)
            self.curves_cont.update()

    def add_marking(self, item):
        self.markings.append(item)
        self.plot.addItem(item, ignoreBounds=True)

    def in_markings(self, item):
        return item in self.markings

    def remove_marking(self, item):
        self.plot.removeItem(item)
        self.markings.remove(item)

    def clear_markings(self):
        self.clear_connect_views()
        for m in self.markings:
            self.plot.removeItem(m)
        self.markings = []

    def add_connected_view(self, vb):
        self.connected_views.append(vb)
        self._update_connected_views()

    def clear_connect_views(self):
        for v in self.connected_views:
            v.clear()  # if the viewbox is not clear the children would be deleted
            self.plot.scene().removeItem(v)
        self.connected_views = []

    def _compute_sample(self, ys):
        if len(ys) > MAX_INSTANCES_DRAWN:
            sample_selection = \
                random.Random(self.sample_seed).sample(range(len(ys)), MAX_INSTANCES_DRAWN)

            # with random selection also show at most MAX_INSTANCES_DRAW elements from the subset
            subset = set(np.where(self.subset_indices)[0])
            subset_to_show = subset - set(sample_selection)
            subset_additional = MAX_INSTANCES_DRAWN - (len(subset) - len(subset_to_show))
            if len(subset_to_show) > subset_additional:
                subset_to_show = \
                    random.Random(self.sample_seed).sample(sorted(subset_to_show), subset_additional)
            sampled_indices = sorted(sample_selection + list(subset_to_show))
        else:
            sampled_indices = list(range(len(ys)))
        return sampled_indices

    def add_curve(self, x, y, pen=None, ignore_bounds=False):
        c = FinitePlotCurveItem(x=x, y=y, pen=pen if pen else self.pen_normal[None])
        self.curves_cont.add_curve(c, ignore_bounds=ignore_bounds)
        # for rescale to work correctly
        if not ignore_bounds:
            self.curves_plotted.append((x, np.array([y])))

    def add_fill_curve(self, x, ylow, yhigh, pen):
        phigh = FinitePlotCurveItem(x, yhigh, pen=pen)
        plow = FinitePlotCurveItem(x, ylow, pen=pen)
        color = pen.color()
        color.setAlphaF(color.alphaF() * 0.3)
        cc = pg.mkBrush(color)
        pfill = pg.FillBetweenItem(plow, phigh, brush=cc)
        pfill.setZValue(10)
        self.curves_cont.add_bounds(phigh)
        self.curves_cont.add_bounds(plow)
        self.curves_cont.add_curve(pfill, ignore_bounds=True)
        # for zoom to work correctly
        self.curves_plotted.append((x, np.array([ylow, yhigh])))

    @staticmethod
    def _generate_pens(color, color_unselected=None, color_selected=None):
        pen_subset = pg.mkPen(color=color, width=1)
        if color_selected is None:
            color_selected = color.darker(135)
            color_selected.setAlphaF(1.0)  # only gains in a sparse space
        pen_selected = pg.mkPen(color=color_selected, width=2, style=QtCore.Qt.DashLine)
        if color_unselected is None:
            color_unselected = color.lighter(160)
        pen_normal = pg.mkPen(color=color_unselected, width=1)
        return pen_normal, pen_selected, pen_subset

    def set_pen_colors(self):
        self.pen_normal.clear()
        self.pen_subset.clear()
        self.pen_selected.clear()
        color_var = self.feature_color
        self.legend.clear()
        palette, legend = False, False
        if color_var is not None:
            discrete_palette = color_var.palette
            palette = [(v, discrete_palette[color_var.to_val(v)]) for v in color_var.values]
            legend = True
        elif self.color_individual:
            palette = [(i, QtGui.QColor(*c)) for i, c in enumerate(self._color_individual_cycle)]
        if palette:
            for v, color in palette:
                color = QtGui.QColor(color)  # copy color
                color.setAlphaF(0.9)
                self.pen_normal[v], self.pen_selected[v], self.pen_subset[v] = \
                    self._generate_pens(color)
                pen = pg.mkPen(color=color)
                brush = pg.mkBrush(color=color)
                if legend:
                    self.legend.addItem(
                        pg.ScatterPlotItem(pen=pen, brush=brush, size=10, symbol="o"), escape(v))
        self.legend.setVisible(bool(self.legend.items))

    def show_individual(self):
        self.show_individual_thread.show()

    def resample_curves(self, seed):
        self.sample_seed = seed
        self.update_view()

    def rescale_current_view_y(self):
        if self.curves_plotted:
            qrect = self.plot.vb.targetRect()
            bleft = qrect.left()
            bright = qrect.right()

            maxcurve = [np.nanmax(ys[:, np.searchsorted(x, bleft):
                                  np.searchsorted(x, bright, side="right")])
                        for x, ys in self.curves_plotted if len(x)]
            mincurve = [np.nanmin(ys[:, np.searchsorted(x, bleft):
                                  np.searchsorted(x, bright, side="right")])
                        for x, ys in self.curves_plotted if len(x)]

            # if all values are nan there is nothing to do
            if bottleneck.allnan(maxcurve):  # allnan(mincurve) would obtain the same result
                return

            ymax = np.nanmax(maxcurve)
            ymin = np.nanmin(mincurve)

            self.plot.vb.setYRange(ymin, ymax, padding=0.0)
            self.plot.vb.pad_current_view_y()

    def viewtype_changed(self):
        if self.viewtype == AVERAGE:
            self.viewtype = INDIVIDUAL
        else:
            self.viewtype = AVERAGE
        self.update_view()

    def show_average(self):
        self.show_average_thread.show()

    def update_view(self):
        if self.viewtype == INDIVIDUAL:
            self.show_individual()
            self.rescale()
        elif self.viewtype == AVERAGE:
            self.show_average()

    def rescale(self):
        if self.rescale_next:
            self.plot.vb.autoRange()

    def set_data(self, data, auto_update=True):
        if self.data is data:
            return
        if data is not None:
            if self.data:
                self.rescale_next = not data.domain == self.data.domain
            else:
                self.rescale_next = True

            self.data = data

            # new data implies that the graph is outdated
            self.clear_graph()

            self.restore_selection_settings()

            # get and sort input data
            x = getx(self.data)
            xsind = np.argsort(x)
            self.data_x = x[xsind]
            self.data_xsind = xsind
            self._set_subset_indices()  # refresh subset indices according to the current subset
            self.make_selection_valid()
        else:
            self.clear_data()
            self.clear_graph()
        if auto_update:
            self.update_view()

    def _set_subset_indices(self):
        ids = self.subset
        if ids is None:
            ids = []
        if self.data:
            self.subset_indices = np.in1d(self.data.ids, ids)

    def set_data_subset(self, ids, auto_update=True):
        self.subset = ids  # an array of indices
        self._set_subset_indices()
        if auto_update:
            self.update_view()

    def select_by_click(self, _):
        clicked_curve = self.highlighted
        if clicked_curve is not None:
            if self.viewtype == INDIVIDUAL:
                self.make_selection([self.sampled_indices[clicked_curve]])
            elif self.viewtype == AVERAGE:
                sel = np.where(self.multiple_curves_info[clicked_curve][2])[0]
                self.make_selection(sel)
        else:
            self.make_selection(None)

    def select_line(self, startp, endp):
        intersected = self.intersect_curves((startp.x(), startp.y()), (endp.x(), endp.y()))
        self.make_selection(intersected if len(intersected) else None)

    def intersect_curves(self, q1, q2):
        x, ys = self.data_x, self.data.X
        if len(x) < 2:
            return []
        x1, x2 = min(q1[0], q2[0]), max(q1[0], q2[0])
        xmin = closestindex(x, x1)
        xmax = closestindex(x, x2, side="right")
        xmin = max(0, xmin - 1)
        xmax = xmax + 2
        sel = np.flatnonzero(intersect_curves_chunked(x, ys, self.data_xsind, q1, q2, xmin, xmax))
        return sel

    def shutdown(self):
        self.show_average_thread.shutdown()
        self.show_individual_thread.shutdown()

    @classmethod
    def migrate_settings_sub(cls, settings, version):
        # manually called from the parent
        if "selected_indices" in settings:
            # transform into list-of-tuples as we do not have data size
            if settings["selected_indices"]:
                settings["selection_group_saved"] = [(a, 1) for a in settings["selected_indices"]]

    @classmethod
    def migrate_context_sub_feature_color(cls, values, version):
        # convert strings to Variable
        name = "feature_color"
        var, vartype = values[name]
        if 0 <= vartype <= 100:
            values[name] = (var, 100 + vartype)