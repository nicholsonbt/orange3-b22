from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems.imageitembase import ImageItemBase
from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItemRegistry


class ImageItem(ImageItemBase):
    id = "Unknown"


    def __init_subclass__(cls, *args, **kwargs):
        ImageItemBase().__init_subclass__(*args, **kwargs)
        ImageItemRegistry.register(cls)

    def __init__(self, image_values=None):
        ImageItemBase.__init__(self, image_values)
        self.imdata = None
        self.domain = None
        self.coords = None
        self.image_values_fixed_levels = None
        

    def set_data(self, imdata, domain, coords, image_values_fixed_levels):
        self.imdata = imdata
        self.domain = domain
        self.coords = coords
        self.image_values_fixed_levels = image_values_fixed_levels


    def get_data(self):
        return self.imdata
