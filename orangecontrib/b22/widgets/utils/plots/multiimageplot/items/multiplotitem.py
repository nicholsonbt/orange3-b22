from Orange.widgets.visualize.utils import plotutils

from orangecontrib.spectroscopy.widgets.owspectra import InteractiveViewBox

from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import MultiPlotMixin




class MultiPlotItem(MultiPlotMixin):
    def __init__(self, parent):
        MultiPlotMixin.__init__(self, parent)

        # The plot of GraphicsObjects.
        self.plot = plotutils.PlotItem(viewBox=InteractiveViewBox(self.parent))
        self.plot.buttonsHidden = True
        self.plot.vb.setAspectLocked()


    @property
    def images(self):
        return self.items


    def set_mode_zooming(self, *args, **kwargs):
        return self.plot.vb.set_mode_zooming(*args, **kwargs)
    

    def set_mode_panning(self, *args, **kwargs):
        return self.plot.vb.set_mode_panning(*args, **kwargs)
    

    def autoRange(self, *args, **kwargs):
        return self.plot.vb.autoRange(*args, **kwargs)
