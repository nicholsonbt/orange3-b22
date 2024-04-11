import numpy as np

from AnyQt import QtGui

from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItem

from orangecontrib.spectroscopy.widgets.owhyper import ImageItemNan




class RasterItem(ImageItem, ImageItemNan):
    id = "Raster (Grid)"


    def __init__(self, *args, **kwargs):
        ImageItem.__init__(self, *args, **kwargs)
        ImageItemNan.__init__(self, *args, **kwargs)


    def get_imdata(self, data):
        imdata = self.get_values(data)[:,::-1]

        return np.rot90(imdata, axes=(0, 1))


    def set_data(self, imdata, domain, coords, image_values_fixed_levels):
        ImageItem.set_data(self, imdata, domain, coords, image_values_fixed_levels)

        self.setOpts(axisOrder='row-major')

        #imdata = self.get_imdata(data)
        imdata = np.rot90(imdata[:,::-1], axes=(0, 1))
        ImageItemNan.setImage(self, imdata, autoLevels=True)

        RasterItem._transform_image(self, domain)
        

    def set_border(self, pen):
        raise NotImplementedError()
    

    def add_menu(self, menu):
        pass


    @staticmethod
    def _transform_image(img, domain):
        r = img.boundingRect().center()

        offset = (-r.x(), -r.y())
        angle = -np.degrees(domain.rotations)

        p_area = domain.pixel_area.copy()
        p_area[p_area < 2] = 2

        scale = domain.real_area / (p_area-1)
        center = domain.real_center

        transform = QtGui.QTransform()
        transform.translate(*center)
        transform.rotate(*angle)
        transform.scale(*scale)
        transform.translate(*offset)
        img.setTransform(transform)

        r = img.boundingRect().center()
        print(scale, center, offset, domain.real_area, p_area)
        print(r)

