from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItemRegistry
from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems.imageitembase import ImageItemBase


class ImageItemFactory:
    @staticmethod
    def generate(plot_type=0):
         assert(isinstance(plot_type, int))
         return ImageItemRegistry.get(plot_type)()


    @staticmethod
    def convert(image_item, plot_type=0):
        plt = ImageItemFactory.generate(plot_type)
        plt.set_image_values(image_item.image_values)

        print(image_item.imdata)

        plt.set_data(image_item.imdata,
                     image_item.domain,
                     image_item.coords,
                     image_item.image_values_fixed_levels)

        return plt
    

    @staticmethod
    def get(index):
        if isinstance(index, int) or isinstance(index, str):
            return ImageItemRegistry.get(index)

        return ImageItemRegistry.get(index.id)

        
