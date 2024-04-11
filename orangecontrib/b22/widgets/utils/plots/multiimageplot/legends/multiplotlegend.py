from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import MultiPlotMixin




class MultiPlotLegend(MultiPlotMixin):
    def __init__(self, parent):
        MultiPlotMixin.__init__(self, parent)


    @property
    def legends(self):
        return self.items
    

    @property
    def positions(self):
        return [legend.swap_meta["pos"] for legend in self.legends]
    
    @property
    def scene_positions(self):
        return [legend.swap_meta["scenePos"] for legend in self.legends]


