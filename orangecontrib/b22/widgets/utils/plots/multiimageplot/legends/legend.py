from AnyQt import QtWidgets, QtGui, QtCore

import traceback, sys

from Orange.widgets.widget import OWComponent

from orangecontrib.spectroscopy.widgets.owhyper import ImageColorLegend

from orangecontrib.b22.widgets.utils.plots.multiimageplot.legends.mixins import ContextMenuMixin, SwappableMixin

from orangecontrib.b22.widgets.utils import pen_colours


class Legend(ImageColorLegend, OWComponent, ContextMenuMixin, SwappableMixin):
    added = QtCore.pyqtSignal()

    def __init__(self, parent, index=-1):
        print("CALLING LEGEND!!!")

        ImageColorLegend.__init__(self)
        OWComponent.__init__(self, parent)

        self.parent = parent
        self._index = index

        ContextMenuMixin.__init__(self)
        SwappableMixin.__init__(self)

        self.added.connect(self.update)


    @property
    def pen(self):
        return QtGui.QPen(pen_colours[self.index], 2)


    @property
    def legends(self):
        return self.parent.legends.legends
    

    @property
    def images(self):
        return self.parent.images.images

    
    @property
    def index(self):
        if self._index == -1:
            raise Exception("ERROR!")

        else:
            return self._index
            
            
    @index.setter
    def index(self, index):
        self._index = index
    

    @property
    def linked_image(self):
        #print(f"B: {self.index}")
        return self.images[self.index]


    def sceneEvent(self, event):
        if isinstance(event, QtWidgets.QGraphicsSceneContextMenuEvent):
            return self.show_context_menu(event.screenPos())

        return super().sceneEvent(event)
    

    def mousePressEvent(self, event):
        SwappableMixin.mousePressEvent(self, event)
        super().mousePressEvent(event)


    def mouseReleaseEvent(self, event):
        SwappableMixin.mouseReleaseEvent(self, event)
        super().mouseReleaseEvent(event)


    def itemChange(self, change, value):
        point = SwappableMixin.itemChange(self, change, value)

        if point is not None:
            return point
        
        return super().itemChange(change, value)
    

    def reset_borders(self):
        for legend in self.legends:
            legend.reset_border()


    def reset_border(self):
        self.rect.setPen(self.pen)


    def highlight(self):
        self.reset_borders()
        pen = QtGui.QPen(QtCore.Qt.black, 2)
        self.rect.setPen(pen)


    def update(self):
        ContextMenuMixin.update(self)
        self.reset_border()
