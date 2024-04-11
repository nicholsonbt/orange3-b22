import sys

from AnyQt import QtCore, QtGui, QtWidgets

import pyqtgraph as pg
from pyqtgraph.graphicsItems.ViewBox import ViewBox

from Orange.widgets.utils.plot import SELECT, PANNING, ZOOMING


from orangecontrib.b22.visuals.components.curveplot.utils import SELECT_SQUARE, SELECT_POLYGON, \
    SELECT_POLYGON_TOLERANCE





class InteractiveViewBox(ViewBox):
    def __init__(self, graph):
        ViewBox.__init__(self, enableMenu=False)
        self.graph = graph
        self.setMouseMode(self.PanMode)
        self.zoomstartpoint = None
        self.current_selection = None
        self.action = PANNING
        self.y_padding = 0
        self.x_padding = 0

        # line for marking selection
        self.selection_line = pg.PlotCurveItem()
        self.selection_line.setPen(pg.mkPen(color=QtGui.QColor(QtCore.Qt.black), width=2, style=QtCore.Qt.DotLine))
        self.selection_line.setZValue(1e9)
        self.selection_line.hide()
        self.addItem(self.selection_line, ignoreBounds=True)

        # yellow marker for ending the polygon
        self.selection_poly_marker = pg.ScatterPlotItem()
        self.selection_poly_marker.setPen(pg.mkPen(color=QtGui.QColor(QtCore.Qt.yellow), width=2))
        self.selection_poly_marker.setSize(SELECT_POLYGON_TOLERANCE*2)
        self.selection_poly_marker.setBrush(None)
        self.selection_poly_marker.setZValue(1e9+1)
        self.selection_poly_marker.hide()
        self.selection_poly_marker.mouseClickEvent = lambda x: x  # ignore mouse clicks
        self.addItem(self.selection_poly_marker, ignoreBounds=True)

        self.sigRangeChanged.connect(self.resized)
        self.sigResized.connect(self.resized)

        self.fixed_range_x = [None, None]
        self.fixed_range_y = [None, None]

        self.tiptexts = None

    def resized(self):
        self.position_tooltip()

    def position_tooltip(self):
        if self.tiptexts:  # if initialized
            self.scene().select_tooltip.setPos(10, self.height())

    def enableAutoRange(self, axis=None, enable=True, x=None, y=None):
        super().enableAutoRange(axis=axis, enable=False, x=x, y=y)

    def update_selection_tooltip(self, modifiers=QtCore.Qt.NoModifier):
        if not self.tiptexts:
            self._create_select_tooltip()
        text = self.tiptexts[QtCore.Qt.NoModifier]
        for mod in [QtCore.Qt.ControlModifier,
                    QtCore.Qt.ShiftModifier,
                    QtCore.Qt.AltModifier]:
            if modifiers & mod:
                text = self.tiptexts.get(mod)
                break
        self.tip_textitem.setHtml(text)
        if self.action in [SELECT, SELECT_SQUARE, SELECT_POLYGON]:
            self.scene().select_tooltip.show()
        else:
            self.scene().select_tooltip.hide()

    def _create_select_tooltip(self):
        scene = self.scene()
        tip_parts = [
            (QtCore.Qt.ControlModifier,
             "{}: Append to group".
             format("Cmd" if sys.platform == "darwin" else "Ctrl")),
            (QtCore.Qt.ShiftModifier, "Shift: Add group"),
            (QtCore.Qt.AltModifier, "Alt: Remove")
        ]
        all_parts = "<center>" + \
                    ", ".join(part for _, part in tip_parts) + \
                    "</center>"
        self.tiptexts = {
            modifier: all_parts.replace(part, "<b>{}</b>".format(part))
            for modifier, part in tip_parts
        }
        self.tiptexts[QtCore.Qt.NoModifier] = all_parts

        self.tip_textitem = text = QtWidgets.QGraphicsTextItem()
        # Set to the longest text
        text.setHtml(self.tiptexts[QtCore.Qt.ControlModifier])
        text.setPos(4, 2)
        r = text.boundingRect()
        text.setTextWidth(r.width())
        rect = QtWidgets.QGraphicsRectItem(0, 0, r.width() + 8, r.height() + 4)
        color = self.graph.palette().color(QtGui.QPalette.Disabled, QtGui.QPalette.Window)
        color.setAlpha(212)
        rect.setBrush(color)
        rect.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        scene.select_tooltip = scene.createItemGroup([rect, text])
        scene.select_tooltip.hide()
        self.position_tooltip()
        self.update_selection_tooltip(QtCore.Qt.NoModifier)

    def safe_update_scale_box(self, buttonDownPos, currentPos):
        x, y = currentPos
        if buttonDownPos[0] == x:
            x += 1
        if buttonDownPos[1] == y:
            y += 1
        self.updateScaleBox(buttonDownPos, pg.Point(x, y))

    # noinspection PyPep8Naming,PyMethodOverriding
    def mouseDragEvent(self, ev, axis=None):
        if ev.button() & QtCore.Qt.RightButton:
            ev.accept()
        if self.action == ZOOMING:
            ev.ignore()
            super().mouseDragEvent(ev, axis=axis)
        elif self.action == PANNING:
            ev.ignore()
            super().mouseDragEvent(ev, axis=axis)
        elif self.action in [SELECT, SELECT_SQUARE, SELECT_POLYGON] \
                and ev.button() == QtCore.Qt.LeftButton \
                and hasattr(self.graph, "selection_type") and self.graph.selection_type:
            pos = self.childGroup.mapFromParent(ev.pos())
            start = self.childGroup.mapFromParent(ev.buttonDownPos())
            if self.current_selection is None:
                self.current_selection = [start]
            if ev.isFinish():
                self._add_selection_point(pos)
            ev.accept()
        else:
            ev.ignore()

    def suggestPadding(self, axis):
        return 0.

    def mouseMovedEvent(self, ev):  # not a Qt event!
        if self.action == ZOOMING and self.zoomstartpoint:
            pos = self.mapFromView(self.mapSceneToView(ev))
            self.updateScaleBox(self.zoomstartpoint, pos)
        if self.action in [SELECT, SELECT_SQUARE, SELECT_POLYGON] and self.current_selection:
            # ev is a position of the whole component (with axes)
            pos = self.childGroup.mapFromParent(self.mapFromView(self.mapSceneToView(ev)))
            if self.action == SELECT:
                self.updateSelectionLine(pos)
            elif self.action == SELECT_SQUARE:
                self.updateSelectionSquare(pos)
            elif self.action == SELECT_POLYGON:
                self.updateSelectionPolygon(pos)

    def updateSelectionLine(self, p2):
        p1 = self.current_selection[0]
        self.selection_line.setData(x=[p1.x(), p2.x()], y=[p1.y(), p2.y()])
        self.selection_line.show()

    def updateSelectionSquare(self, p2):
        p1 = self.current_selection[0]
        self.selection_line.setData(x=[p1.x(), p1.x(), p2.x(), p2.x(), p1.x()],
                                    y=[p1.y(), p2.y(), p2.y(), p1.y(), p1.y()])
        self.selection_line.show()

    def _distance_pixels(self, p1, p2):
        xpixel, ypixel = self.viewPixelSize()
        dx = (p1.x() - p2.x()) / xpixel
        dy = (p1.y() - p2.y()) / ypixel
        return (dx**2 + dy**2)**0.5

    def updateSelectionPolygon(self, p):
        first = self.current_selection[0]
        polygon = self.current_selection + [p]
        self.selection_line.setData(x=[e.x() for e in polygon],
                                    y=[e.y() for e in polygon])
        self.selection_line.show()
        if self._distance_pixels(first, p) < SELECT_POLYGON_TOLERANCE:
            self.selection_poly_marker.setData(x=[first.x()], y=[first.y()])
            self.selection_poly_marker.show()
        else:
            self.selection_poly_marker.hide()

    def keyPressEvent(self, ev):
        # cancel current selection process
        if self.action in [SELECT, SELECT_SQUARE, SELECT_POLYGON] and \
                ev.key() in [QtCore.Qt.Key_Escape]:
            self.set_mode_panning()
            ev.accept()
        else:
            self.update_selection_tooltip(ev.modifiers())
            ev.ignore()

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.update_selection_tooltip(event.modifiers())

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and \
                (self.action == ZOOMING or self.action in [SELECT, SELECT_SQUARE, SELECT_POLYGON]):
            ev.accept()
            self.set_mode_panning()
        elif ev.button() == QtCore.Qt.RightButton:
            ev.accept()
            self.autoRange()
        if self.action != ZOOMING and self.action not in [SELECT, SELECT_SQUARE, SELECT_POLYGON] \
                and ev.button() == QtCore.Qt.LeftButton and \
                hasattr(self.graph, "selection_type") and self.graph.selection_type:
            pos = self.childGroup.mapFromParent(ev.pos())
            self.graph.select_by_click(pos)
            ev.accept()
        if self.action == ZOOMING and ev.button() == QtCore.Qt.LeftButton:
            if self.zoomstartpoint is None:
                self.zoomstartpoint = ev.pos()
            else:
                self.updateScaleBox(self.zoomstartpoint, ev.pos())
                self.rbScaleBox.hide()
                ax = QtCore.QRectF(pg.Point(self.zoomstartpoint), pg.Point(ev.pos()))
                ax = self.childGroup.mapRectFromParent(ax)
                self.showAxRect(ax)
                self.axHistoryPointer += 1
                self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
                self.set_mode_panning()
            ev.accept()
        if self.action in [SELECT, SELECT_SQUARE, SELECT_POLYGON] \
                and ev.button() == QtCore.Qt.LeftButton and self.graph.selection_type:
            pos = self.childGroup.mapFromParent(ev.pos())
            if self.current_selection is None:
                self.current_selection = [pos]
            else:
                self._add_selection_point(pos)
            ev.accept()

    def _add_selection_point(self, pos):
        startp = self.current_selection[0]
        if self.action == SELECT:
            self.graph.select_line(startp, pos)
            self.set_mode_panning()
        elif self.action == SELECT_SQUARE:
            self.graph.select_square(startp, pos)
            self.set_mode_panning()
        elif self.action == SELECT_POLYGON:
            self.polygon_point_click(pos)

    def polygon_point_click(self, p):
        first = self.current_selection[0]
        if self._distance_pixels(first, p) < SELECT_POLYGON_TOLERANCE:
            self.current_selection.append(first)
            self.graph.select_polygon(self.current_selection)
            self.set_mode_panning()
        else:
            self.current_selection.append(p)

    def showAxRect(self, ax):
        super().showAxRect(ax)
        if self.action == ZOOMING:
            self.set_mode_panning()

    def pad_current_view_y(self):
        if self.y_padding:
            qrect = self.targetRect()
            self.setYRange(qrect.bottom(), qrect.top(), padding=self.y_padding)

    def pad_current_view_x(self):
        if self.x_padding:
            qrect = self.targetRect()
            self.setXRange(qrect.left(), qrect.right(), padding=self.x_padding)

    def autoRange(self):
        super().autoRange()
        self.pad_current_view_y()
        self.pad_current_view_x()

    def is_view_locked(self):
        return not all(a is None for a in self.fixed_range_x + self.fixed_range_y)

    def setRange(self, rect=None, xRange=None, yRange=None, **kwargs):
        """ Always respect limitations in fixed_range_x and _y. """

        if not self.is_view_locked():
            super().setRange(rect=rect, xRange=xRange, yRange=yRange, **kwargs)
            return

        # if any limit is defined disregard padding
        kwargs["padding"] = 0

        if rect is not None:
            rect = QtCore.QRectF(rect)
            if self.fixed_range_x[0] is not None:
                rect.setLeft(self.fixed_range_x[0])
            if self.fixed_range_x[1] is not None:
                rect.setRight(self.fixed_range_x[1])
            if self.fixed_range_y[0] is not None:
                rect.setTop(self.fixed_range_y[0])
            if self.fixed_range_y[1] is not None:
                rect.setBottom(self.fixed_range_y[1])

        if xRange is not None:
            xRange = list(xRange)
            if self.fixed_range_x[0] is not None:
                xRange[0] = self.fixed_range_x[0]
            if self.fixed_range_x[1] is not None:
                xRange[1] = self.fixed_range_x[1]

        if yRange is not None:
            yRange = list(yRange)
            if self.fixed_range_y[0] is not None:
                yRange[0] = self.fixed_range_y[0]
            if self.fixed_range_y[1] is not None:
                yRange[1] = self.fixed_range_y[1]

        super().setRange(rect=rect, xRange=xRange, yRange=yRange, **kwargs)

    def cancel_zoom(self):
        self.setMouseMode(self.PanMode)
        self.rbScaleBox.hide()
        self.zoomstartpoint = None
        self.action = PANNING
        self.unsetCursor()
        self.update_selection_tooltip()

    def set_mode_zooming(self):
        self.set_mode_panning()
        self.setMouseMode(self.RectMode)
        self.action = ZOOMING
        self.setCursor(QtCore.Qt.CrossCursor)
        self.update_selection_tooltip()

    def set_mode_panning(self):
        self.cancel_zoom()
        self.cancel_select()

    def cancel_select(self):
        self.setMouseMode(self.PanMode)
        self.selection_line.hide()
        self.selection_poly_marker.hide()
        self.current_selection = None
        self.action = PANNING
        self.unsetCursor()
        self.update_selection_tooltip()

    def set_mode_select(self):
        self.set_mode_panning()
        self.setMouseMode(self.RectMode)
        self.action = SELECT
        self.setCursor(QtCore.Qt.CrossCursor)
        self.update_selection_tooltip()

    def set_mode_select_square(self):
        self.set_mode_panning()
        self.setMouseMode(self.RectMode)
        self.action = SELECT_SQUARE
        self.setCursor(QtCore.Qt.CrossCursor)
        self.update_selection_tooltip()

    def set_mode_select_polygon(self):
        self.set_mode_panning()
        self.setMouseMode(self.RectMode)
        self.action = SELECT_POLYGON
        self.setCursor(QtCore.Qt.CrossCursor)
        self.update_selection_tooltip()