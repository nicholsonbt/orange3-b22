import pyqtgraph as pg

import numpy as np

from AnyQt import QtCore

from Orange.widgets import settings

from orangecontrib.b22.widgets.utils.plots.multiimageplot.items import MultiPlotItem
from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItemFactory, ImageItem
from orangecontrib.b22.widgets.utils.plots.multiimageplot.legends import MultiPlotLegend, Legend
from Orange.widgets.utils.concurrent import TaskState, ConcurrentMixin

from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import ComputeImageMixin

from Orange.widgets.widget import OWComponent

from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import SettingsHandlerMixin


class MultiPlotLayout(pg.GraphicsLayout, OWComponent, SettingsHandlerMixin, ComputeImageMixin, ConcurrentMixin):
    image_updated = QtCore.pyqtSignal()


    images = settings.SettingProvider(MultiPlotItem)
    legends = settings.SettingProvider(MultiPlotLegend)
    legend = settings.SettingProvider(Legend)
    image = settings.SettingProvider(ImageItem)


    def __init__(self, parent):
        pg.GraphicsLayout.__init__(self)
        OWComponent.__init__(self, parent)
        SettingsHandlerMixin.__init__(self)
        ConcurrentMixin.__init__(self)

        self.parent = parent

        self.parent.datas_set.connect(self.datas_set)
        self.parent.datas_removed.connect(self.datas_removed)
        self.parent.datas_inserted.connect(self.datas_inserted)
        self.parent.multispectra_updated.connect(self.multispectra_updated)
        
        self.images = MultiPlotItem(self)
        self.legends = MultiPlotLegend(self)

        self.order = []

        self.addItem(self.images.plot)
        self.addItem(self.legends.plot)




    def multispectra_updated(self, index, flag):
        print("Redrawing data 3")
        if flag:
            print(f"Drawing image {index}.")
            self.draw_data(index, image_type=0)
        else:
            print("Updating image.")
        self.refresh_order()
        print(1)
        self.images.autoRange()
        self.images.set_mode_panning()
        print(2)


    def datas_set(self):
        # Redraw all data.
        self.order = []
        self.images.clear()
        self.legends.clear()

        for i in range(len(self.datas)):
            self.insert(i)


    def datas_removed(self, index):
        # Remove a specific image.
        self.remove(index)


    def datas_inserted(self, index):
        # Insert a new image.
        self.insert(index)


    @property
    def datas(self):
        return self.parent.parent.datas
    
    @property
    def attr_x(self):
        return self.parent.attr_x
    
    @property
    def attr_y(self):
        return self.parent.attr_y
    

    def convert_to_type(self, index, plot_type):
        self.images.images[index] = ImageItemFactory.convert(self.images.images[index], plot_type)
        self.legends.legends[index] = Legend(self, index)
        self.legends.legends[index].added.emit()
        self.refresh_order()
    

    # def update(self, index=None):
    #     if not index:
    #         self.update_all()

    #     else:
    #         self.update_at(index)


    def reorder(self):
        pass
        


    def remove(self, index):
        self.images.pop_item(self.order[index])
        self.legends.pop_item(self.order[index])
        self.order.pop(index)

        self.reorder()


    def insert(self, index, image_type=0):
        image = ImageItemFactory.generate(image_type)
        legend = Legend(self, index)

        self.images.add_item(image, index)
        self.legends.add_item(legend, index)
        self.order.append(index)
        legend.added.emit()

        print(f"Order: {self.order}")

        self.refresh_order()
        # self.draw_data(index, image_type)


    # def update_all(self):
    #     self.images.plot.clear()
    #     self.legends.plot.clear()

    #     if self.attr_x and self.attr_y:
    #         for index in range(len(self.datas)):
    #             self._update_at(index)

    #         self.refresh()


    # def update_at(self, index):
    #     if self.attr_x and self.attr_y:
    #         self._update_at(index)
    #         self.refresh()










    def refresh_order(self):
        self.images.refresh_order()
        self.legends.refresh_order()


    def move_plot(self, old_index, new_index):
        item = self.order.pop(old_index)
        
        self.order.insert(new_index, item)
        self.refresh_order()


    def draw_data(self, index, image_type=0):
        if self.datas is None or len(self.datas) <= index or self.datas[index] == None:
            return
        
        print("draw_data")
        plane = self.datas[index].squash_to([self.attr_x, self.attr_y])
        print("squashed")
        
        self.start(self.compute_image, 
                   index,
                   image_type,
                   plane,
                   self.image_values(index),
                   self.image_values_fixed_levels(index),
                   )
        

    
        

    def image_values(self, index):
        return self.parent.image_values(index)
    
    def image_values_fixed_levels(self, index):
        return self.parent.image_values_fixed_levels(index)
